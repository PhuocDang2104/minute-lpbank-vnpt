from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional

import grpc
import httpx

from app.core.config import get_settings


settings = get_settings()

PROTO_DIR = Path(__file__).resolve().parents[2] / "protos_compiled"
if PROTO_DIR.exists():
    sys.path.insert(0, str(PROTO_DIR))


_proto_import_error: Optional[Exception] = None
try:
    from protos_compiled import vnpt_asr_pb2 as rasr
    from protos_compiled import vnpt_asr_pb2_grpc as rasr_srv
    from protos_compiled import vnpt_audio_pb2 as ra
except Exception as exc:  # pragma: no cover - optional dependency until SmartVoice is enabled
    rasr = None  # type: ignore[assignment]
    rasr_srv = None  # type: ignore[assignment]
    ra = None  # type: ignore[assignment]
    _proto_import_error = exc


@dataclass(frozen=True)
class SmartVoiceStreamingConfig:
    language_code: str = "vi-VN"
    sample_rate_hz: int = 16000
    model: str = ""
    interim_results: bool = True
    enable_word_time_offsets: bool = True


@dataclass(frozen=True)
class SmartVoiceResult:
    text: str
    is_final: bool
    confidence: float
    time_start: Optional[float]
    time_end: Optional[float]
    lang: str
    speaker: str = "SPEAKER_01"


def is_smartvoice_configured() -> bool:
    return bool(settings.smartvoice_grpc_endpoint)


def _smartvoice_time_to_seconds(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000.0
    seconds = getattr(value, "seconds", None)
    if seconds is None:
        return None
    nanos = float(getattr(value, "nanos", 0) or 0.0)
    return float(seconds) + (nanos / 1_000_000_000.0)


def _extract_token(resp_json: Any) -> Optional[str]:
    if not isinstance(resp_json, dict):
        return None
    for key in ("access_token", "token"):
        if isinstance(resp_json.get(key), str) and resp_json.get(key):
            return resp_json[key]
    data = resp_json.get("data")
    if isinstance(data, dict):
        for key in ("access_token", "token"):
            if isinstance(data.get(key), str) and data.get(key):
                return data[key]
    return None


async def _fetch_access_token() -> Optional[str]:
    if settings.smartvoice_access_token:
        return settings.smartvoice_access_token

    if settings.smartvoice_auth_url and settings.smartvoice_token_id and settings.smartvoice_token_key:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                settings.smartvoice_auth_url,
                json={
                    "token_id": settings.smartvoice_token_id,
                    "token_key": settings.smartvoice_token_key,
                },
            )
            resp.raise_for_status()
            token = _extract_token(resp.json())
            if token:
                return token
        raise RuntimeError("SmartVoice auth response missing access_token")

    return None


async def _build_metadata() -> list[tuple[str, str]]:
    metadata: list[tuple[str, str]] = []
    token = await _fetch_access_token()
    if token:
        metadata.append(("authorization", f"Bearer {token}"))
    if settings.smartvoice_token_id:
        metadata.append(("token-id", settings.smartvoice_token_id))
    if settings.smartvoice_token_key:
        metadata.append(("token-key", settings.smartvoice_token_key))
    return metadata


def stream_recognize(
    audio_queue: "asyncio.Queue[Optional[bytes]]",
    config: SmartVoiceStreamingConfig,
) -> AsyncIterator[SmartVoiceResult]:
    return _stream_recognize_impl(audio_queue, config)


async def _stream_recognize_impl(
    audio_queue: "asyncio.Queue[Optional[bytes]]",
    config: SmartVoiceStreamingConfig,
) -> AsyncIterator[SmartVoiceResult]:
    """
    Stream PCM audio to SmartVoice (gRPC) and yield partial/final transcript results.

    Notes:
    - This implementation is intentionally minimal and expects SmartVoice to be compatible with
      Google Speech-to-Text `StreamingRecognize` proto. Configure endpoint/auth via env.
    """
    if rasr is None or rasr_srv is None or ra is None:
        raise RuntimeError(f"SmartVoice protos not available: {_proto_import_error}")
    if not settings.smartvoice_grpc_endpoint:
        raise RuntimeError("SMARTVOICE_GRPC_ENDPOINT is not set")

    metadata = await _build_metadata()
    insecure = os.getenv("SMARTVOICE_INSECURE", "0").lower() in {"1", "true", "yes"}
    channel = grpc.aio.insecure_channel(settings.smartvoice_grpc_endpoint) if insecure else grpc.aio.secure_channel(
        settings.smartvoice_grpc_endpoint, grpc.ssl_channel_credentials()
    )

    async def request_gen():
        recognition_config = rasr.RecognitionConfig(
            language_code=config.language_code or "vi-VN",
            encoding=ra.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=config.sample_rate_hz,
            max_alternatives=1,
            enable_automatic_punctuation=False,
            enable_word_time_offsets=config.enable_word_time_offsets,
            audio_channel_count=1,
            model=config.model or settings.smartvoice_model or "fast_streaming",
        )
        streaming_config = rasr.StreamingRecognitionConfig(
            config=recognition_config,
            interim_results=config.interim_results,
        )
        yield rasr.StreamingRecognizeRequest(streaming_config=streaming_config)
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            yield rasr.StreamingRecognizeRequest(audio_content=chunk)

    async with channel:
        client = rasr_srv.VnptSpeechRecognitionStub(channel)
        responses = client.StreamingRecognize(request_gen(), metadata=metadata)
        async for resp in responses:
            for result in getattr(resp, "results", []) or []:
                alternatives = getattr(result, "alternatives", None) or []
                if not alternatives:
                    continue
                alt = alternatives[0]
                text = (getattr(alt, "transcript", "") or "").strip()
                if not text:
                    continue
                confidence = float(getattr(alt, "confidence", 0.0) or 0.0)

                time_start = None
                time_end = None
                words = getattr(alt, "words", None) or []
                if words:
                    try:
                        time_start = _smartvoice_time_to_seconds(words[0].start_time)
                        time_end = _smartvoice_time_to_seconds(words[-1].end_time)
                    except Exception:
                        time_start = None
                        time_end = None

                lang = (config.language_code.split("-")[0] if config.language_code else "vi").lower()
                yield SmartVoiceResult(
                    text=text,
                    is_final=bool(getattr(result, "is_final", False)),
                    confidence=confidence if confidence else 1.0,
                    time_start=time_start,
                    time_end=time_end,
                    lang=lang,
                )
