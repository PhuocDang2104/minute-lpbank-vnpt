"""
VNPT Speech-to-Text Service
Non-streaming transcription using VNPT SmartVoice API
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import grpc
import wave

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

PROTO_DIR = Path(__file__).resolve().parents[2] / "protos_compiled"
if PROTO_DIR.exists():
    sys.path.insert(0, str(PROTO_DIR))

_proto_import_error: Optional[Exception] = None
try:
    from protos_compiled import vnpt_asr_pb2 as rasr
    from protos_compiled import vnpt_asr_pb2_grpc as rasr_srv
    from protos_compiled import vnpt_audio_pb2 as ra
except Exception as exc:
    rasr = None  # type: ignore[assignment]
    rasr_srv = None  # type: ignore[assignment]
    ra = None  # type: ignore[assignment]
    _proto_import_error = exc


@dataclass
class TranscriptionResult:
    """Result of audio transcription"""
    text: str
    confidence: float
    language: str
    segments: List[Dict[str, Any]]  # List of segments with time_start, time_end, text, confidence
    words: Optional[List[Dict[str, Any]]] = None  # Optional word-level timestamps


def _build_metadata() -> List[Tuple[str, str]]:
    """Build gRPC metadata for authentication"""
    metadata = []
    
    access_token = settings.smartvoice_access_token or os.getenv("SMARTVOICE_ACCESS_TOKEN", "")
    token_id = settings.smartvoice_token_id or os.getenv("SMARTVOICE_TOKEN_ID", "")
    token_key = settings.smartvoice_token_key or os.getenv("SMARTVOICE_TOKEN_KEY", "")
    
    if access_token:
        metadata.append(("authorization", f"Bearer {access_token}"))
    if token_id:
        metadata.append(("token-id", token_id))
    if token_key:
        metadata.append(("token-key", token_key))
    
    return metadata


def _smartvoice_time_to_seconds(value: Any) -> Optional[float]:
    """Convert SmartVoice time value to seconds"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000.0
    seconds = getattr(value, "seconds", None)
    if seconds is None:
        return None
    nanos = float(getattr(value, "nanos", 0) or 0.0)
    return float(seconds) + (nanos / 1_000_000_000.0)


async def transcribe_audio_file(
    audio_path: str | Path,
    language_code: str = "vi-VN",
    model: Optional[str] = None,
    enable_word_time_offsets: bool = True,
) -> TranscriptionResult:
    """
    Transcribe audio file using VNPT SmartVoice Recognize API (non-streaming).
    
    Args:
        audio_path: Path to audio file (WAV format, 16kHz mono recommended)
        language_code: Language code (default: "vi-VN")
        model: Model name (default: from settings)
        enable_word_time_offsets: Enable word-level timestamps
        
    Returns:
        TranscriptionResult with text, confidence, segments, and words
        
    Raises:
        RuntimeError if protos not available or API call fails
    """
    if rasr is None or rasr_srv is None or ra is None:
        raise RuntimeError(f"SmartVoice protos not available: {_proto_import_error}")
    if not settings.smartvoice_grpc_endpoint:
        raise RuntimeError("SMARTVOICE_GRPC_ENDPOINT is not set")
    
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Read audio file
    try:
        with wave.open(str(audio_path), "rb") as wf:
            sample_rate = wf.getframerate()
            audio_data = wf.readframes(wf.getnframes())
    except Exception as e:
        logger.error(f"Failed to read audio file: {e}")
        raise RuntimeError(f"Failed to read audio file: {e}")
    
    # Build metadata
    metadata = _build_metadata()
    
    # Build recognition config
    recognition_config = rasr.RecognitionConfig(
        language_code=language_code,
        encoding=ra.AudioEncoding.LINEAR_PCM,
        sample_rate_hertz=sample_rate,
        max_alternatives=1,
        enable_automatic_punctuation=False,
        enable_word_time_offsets=enable_word_time_offsets,
        audio_channel_count=1,
        model=model or settings.smartvoice_model or "fast_streaming",
    )
    
    # Build request
    request = rasr.RecognizeRequest(
        config=recognition_config,
        audio=audio_data,
    )
    
    # Call API
    insecure = os.getenv("SMARTVOICE_INSECURE", "0").lower() in {"1", "true", "yes"}
    channel = grpc.aio.insecure_channel(settings.smartvoice_grpc_endpoint) if insecure else grpc.aio.secure_channel(
        settings.smartvoice_grpc_endpoint, grpc.ssl_channel_credentials()
    )
    
    try:
        async with channel:
            client = rasr_srv.VnptSpeechRecognitionStub(channel)
            response = await client.Recognize(request, metadata=metadata)
            
            # Parse response
            segments = []
            words_list = []
            full_text_parts = []
            total_confidence = 0.0
            segment_count = 0
            
            for result in getattr(response, "results", []) or []:
                alternatives = getattr(result, "alternatives", None) or []
                if not alternatives:
                    continue
                
                alt = alternatives[0]
                text = (getattr(alt, "transcript", "") or "").strip()
                if not text:
                    continue
                
                confidence = float(getattr(alt, "confidence", 0.0) or 0.0)
                total_confidence += confidence
                segment_count += 1
                full_text_parts.append(text)
                
                # Get word-level timestamps
                words = getattr(alt, "words", None) or []
                segment_words = []
                
                time_start = None
                time_end = None
                if words:
                    try:
                        time_start = _smartvoice_time_to_seconds(words[0].start_time)
                        time_end = _smartvoice_time_to_seconds(words[-1].end_time)
                        
                        for word_info in words:
                            word_start = _smartvoice_time_to_seconds(word_info.start_time)
                            word_end = _smartvoice_time_to_seconds(word_info.end_time)
                            word_text = getattr(word_info, "word", "") or ""
                            
                            segment_words.append({
                                "word": word_text,
                                "start_time": word_start,
                                "end_time": word_end,
                            })
                            words_list.append({
                                "word": word_text,
                                "start_time": word_start,
                                "end_time": word_end,
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse word timestamps: {e}")
                
                segments.append({
                    "text": text,
                    "confidence": confidence,
                    "time_start": time_start,
                    "time_end": time_end,
                    "words": segment_words,
                })
            
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            full_text = " ".join(full_text_parts)
            lang = language_code.split("-")[0].lower() if language_code else "vi"
            
            return TranscriptionResult(
                text=full_text,
                confidence=avg_confidence,
                language=lang,
                segments=segments,
                words=words_list if enable_word_time_offsets else None,
            )
            
    except grpc.RpcError as e:
        logger.error(f"gRPC error during transcription: {e}")
        raise RuntimeError(f"Transcription failed: {e.code()} - {e.details()}")
    except Exception as e:
        logger.error(f"Unexpected error during transcription: {e}")
        raise RuntimeError(f"Transcription failed: {str(e)}")

