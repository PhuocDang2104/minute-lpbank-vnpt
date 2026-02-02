"""
Quick SmartVoice gRPC streaming test.

Usage:
  cd vnpt_ai_hackathon/backend/tests
  python run_smartvoice_streaming.py

Env:
  SMARTVOICE_GRPC_ENDPOINT=<host:port>
  SMARTVOICE_ACCESS_TOKEN=<access_token>      # Bearer token
  SMARTVOICE_TOKEN_ID=<token_id>              # optional, if server expects metadata
  SMARTVOICE_TOKEN_KEY=<token_key>            # optional, if server expects metadata
  SMARTVOICE_AUDIO_PATH=<path/to/audio>       # default: Chapter-1-Conversation-2.mp3
  SMARTVOICE_INSECURE=1                       # set to use insecure_channel (else TLS)
"""

import os
import sys
import wave
import tempfile
import subprocess
from pathlib import Path
from typing import Iterable

import grpc

import os, sys
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "protos_compiled"))
from protos_compiled import vnpt_asr_pb2 as rasr
from protos_compiled import vnpt_asr_pb2_grpc as rasr_srv
from protos_compiled import vnpt_audio_pb2 as ra


DEFAULT_AUDIO = Path(
    r"C:\Users\ADMIN\Desktop\vnpt_meetmate\vnpt_ai_hackathon\backend\tests\resources\eLabs-1.wav"
)
CHUNK = 2048


def _convert_to_wav(src: Path) -> Path:
    """Convert input audio to mono 16k PCM WAV if not already WAV."""
    if src.suffix.lower() == ".wav":
        return src
    out = Path(tempfile.gettempdir()) / f"smartvoice_tmp_{src.stem}_16k.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        str(out),
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({res.returncode}): {res.stderr.decode('utf-8', 'ignore')}")
    return out


def listen_print_loop(responses: Iterable[rasr.StreamingRecognizeResponse], show_intermediate: bool = True) -> None:
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        partial_transcript = ""
        for result in response.results:
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if show_intermediate:
                if not result.is_final:
                    partial_transcript += transcript
                else:
                    overwrite_chars = " " * max(0, num_chars_printed - len(transcript))
                    print("## " + transcript + overwrite_chars + "\n")
                    num_chars_printed = 0

            else:
                if result.is_final:
                    sys.stdout.buffer.write(transcript.encode("utf-8"))
                    sys.stdout.flush()
                    print("\n")

        if show_intermediate and partial_transcript != "":
            overwrite_chars = " " * max(0, num_chars_printed - len(partial_transcript))
            sys.stdout.write(">> " + partial_transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(partial_transcript) + 3


def request_generator(wf: wave.Wave_read, streaming_config: rasr.StreamingRecognitionConfig):
    yield rasr.StreamingRecognizeRequest(streaming_config=streaming_config)
    data = wf.readframes(CHUNK)
    while len(data) > 0:
        yield rasr.StreamingRecognizeRequest(audio_content=data)
        data = wf.readframes(CHUNK)


def main() -> int:
    audio_file = Path(os.getenv("SMARTVOICE_AUDIO_PATH", DEFAULT_AUDIO))
    if not audio_file.exists():
        print(f"[ERR] Audio not found: {audio_file}")
        return 1

    try:
        wav_path = _convert_to_wav(audio_file)
    except Exception as exc:
        print(f"[ERR] Failed to prepare audio: {exc}")
        return 1

    server = os.getenv("SMARTVOICE_GRPC_ENDPOINT", "").strip()
    if not server:
        print("[ERR] SMARTVOICE_GRPC_ENDPOINT is not set (host:port).")
        return 1

    access_token = os.getenv("SMARTVOICE_ACCESS_TOKEN", "").strip()
    token_id = os.getenv("SMARTVOICE_TOKEN_ID", "").strip()
    token_key = os.getenv("SMARTVOICE_TOKEN_KEY", "").strip()

    metadata = []
    if access_token:
        metadata.append(("authorization", f"Bearer {access_token}"))
    if token_id:
        metadata.append(("token-id", token_id))
    if token_key:
        metadata.append(("token-key", token_key))

    insecure = os.getenv("SMARTVOICE_INSECURE", "0").lower() in {"1", "true", "yes"}
    channel = grpc.insecure_channel(server) if insecure else grpc.secure_channel(server, grpc.ssl_channel_credentials())
    client = rasr_srv.VnptSpeechRecognitionStub(channel)

    with wave.open(str(wav_path), "rb") as wf:
        config = rasr.RecognitionConfig(
            language_code="vi-VN",
            encoding=ra.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=wf.getframerate(),
            max_alternatives=1,
            enable_automatic_punctuation=False,
        )
        streaming_config = rasr.StreamingRecognitionConfig(config=config, interim_results=True)

        print(f"[INFO] Streaming {wav_path} -> {server}")
        print(f"[INFO] metadata keys: {[k for k, _ in metadata]}")
        responses = client.StreamingRecognize(request_generator(wf, streaming_config), metadata=metadata)
        listen_print_loop(responses, show_intermediate=True)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
