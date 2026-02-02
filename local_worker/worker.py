import os
import sys
from pathlib import Path
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from pyannote.audio import Pipeline

from audio_buffer import AudioBuffer
from api_client import APIClient

DOTENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH, override=True)


def _get_required_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        sys.exit(f"{name} is required (checked env and {DOTENV_PATH})")
    return value


HF_TOKEN = _get_required_env("HF_TOKEN")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api/v1")
SESSION_ID = _get_required_env("SESSION_ID")
TIME_OFFSET_SEC = float(os.getenv("DIARIZATION_OFFSET_SEC", "0.0"))

print(f"Loaded env from {DOTENV_PATH}")
print(
    f"SESSION_ID={SESSION_ID} | BACKEND_BASE_URL={BACKEND_BASE_URL} | "
    f"HF_TOKEN_present={bool(HF_TOKEN)} | DIARIZATION_OFFSET_SEC={TIME_OFFSET_SEC}"
)

try:
    print("Loading diarization model pyannote/speaker-diarization ...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization",
        use_auth_token=HF_TOKEN,
    )
except Exception as exc:
    sys.exit(f"Failed to load diarization model: {exc}")

buffer = AudioBuffer()
api = APIClient(
    base_url=BACKEND_BASE_URL,
    session_id=SESSION_ID,
)


def audio_callback(indata, frames, time, status):
    samples = indata[:, 0].astype(np.float32)
    buffer.push(samples)

    popped = buffer.pop_chunk()
    if popped is None:
        return

    chunk, chunk_start = popped
    base_time = float(chunk_start)
    if base_time < 0:
        base_time = 0.0

    diarization = pipeline(
        {
            "waveform": chunk,
            "sample_rate": 16000,
        }
    )

    segments = []
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "speaker": speaker,
                "start": float(segment.start + base_time + TIME_OFFSET_SEC),
                "end": float(segment.end + base_time + TIME_OFFSET_SEC),
                "confidence": 1.0,
            }
        )

    if segments:
        api.send_segments(segments)


print("🎙️ Diarization worker started")

with sd.InputStream(
    samplerate=16000,
    channels=1,
    callback=audio_callback,
):
    while True:
        pass
