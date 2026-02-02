import asyncio
import json
import os
import time
import uuid
import wave

import audioop
import httpx
import websockets

"""
Manual test script (not a pytest test).

Goal: stream a local WAV into MeetMate audio ingress WS and verify that
`transcript_event` arrives on frontend WS.

This script will:
1) POST /api/v1/sessions (optionally with a fixed session_id)
2) POST /api/v1/sessions/{session_id}/sources to obtain audio_ingest_token
3) Open WS /api/v1/ws/frontend/{session_id} to print transcript/state events
4) Open WS /api/v1/ws/audio/{session_id}?token=... and stream audio frames

WAV notes:
- Spec expects PCM_S16LE mono 16kHz. The provided eLabs-1.wav is 44.1kHz mono 16-bit,
  so we resample to 16kHz before streaming.
"""

HTTP_BASE = os.getenv("MEETMATE_HTTP_BASE", "http://localhost:8000").rstrip("/")
SESSION_ID = os.getenv("MEETMATE_SESSION_ID", "").strip() or str(uuid.uuid4())
WAV_PATH = os.getenv(
    "MEETMATE_WAV_PATH",
    os.path.join(os.path.dirname(__file__), "resources", "eLabs-1.wav"),
)
LANGUAGE_CODE = os.getenv("MEETMATE_LANGUAGE_CODE", "vi-VN")
FRAME_MS = int(os.getenv("MEETMATE_FRAME_MS", "250"))
CREATE_SESSION = os.getenv("MEETMATE_CREATE_SESSION", "1").strip() not in ("0", "false", "False")
REGISTER_SOURCE = os.getenv("MEETMATE_REGISTER_SOURCE", "1").strip() not in ("0", "false", "False")
AUDIO_INGEST_TOKEN = os.getenv("MEETMATE_AUDIO_INGEST_TOKEN", "").strip()

TARGET_SR = int(os.getenv("MEETMATE_TARGET_SR", "16000"))
POST_STREAM_WAIT_SEC = float(os.getenv("MEETMATE_POST_STREAM_WAIT_SEC", "3.0"))


def _ws_base_from_http(http_base: str) -> str:
    if http_base.startswith("https://"):
        return "wss://" + http_base[len("https://") :]
    if http_base.startswith("http://"):
        return "ws://" + http_base[len("http://") :]
    # fallback: assume already ws/wss or host:port
    if http_base.startswith("ws://") or http_base.startswith("wss://"):
        return http_base
    return "ws://" + http_base


async def _ensure_session() -> dict:
    url = f"{HTTP_BASE}/api/v1/sessions"
    payload = {
        "session_id": SESSION_ID,
        "language_code": LANGUAGE_CODE,
        "target_sample_rate_hz": TARGET_SR,
        "audio_encoding": "PCM_S16LE",
        "channels": 1,
        "realtime": True,
        "interim_results": True,
        "enable_word_time_offsets": True,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


async def _ensure_audio_token() -> str:
    url = f"{HTTP_BASE}/api/v1/sessions/{SESSION_ID}/sources"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        return resp.json()["audio_ingest_token"]


def _to_pcm16_mono(data: bytes, in_width: int, in_channels: int) -> bytes:
    pcm = data
    if in_width != 2:
        pcm = audioop.lin2lin(pcm, in_width, 2)
        in_width = 2
    if in_channels != 1:
        pcm = audioop.tomono(pcm, in_width, 0.5, 0.5)
    return pcm


async def _listen_frontend(stop: asyncio.Event, ws_base: str):
    url = f"{ws_base}/api/v1/ws/frontend/{SESSION_ID}"
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5, max_size=8 * 1024 * 1024) as ws:
        while not stop.is_set():
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
            except asyncio.TimeoutError:
                continue
            print("FEED ⬅️", msg)


async def _stream_audio(stop: asyncio.Event, ws_base: str):
    nonlocal_frame_ms = {"value": FRAME_MS}

    async def recv_audio_events(ws):
        while True:
            try:
                msg = await ws.recv()
            except Exception:
                return
            try:
                data = json.loads(msg) if isinstance(msg, str) else None
            except Exception:
                data = None
            if isinstance(data, dict) and data.get("event") == "throttle":
                suggested = data.get("suggested_frame_ms")
                if isinstance(suggested, int) and suggested > 0:
                    nonlocal_frame_ms["value"] = suggested
                    print("AUDIO ⚠️ throttle:", data)
            elif isinstance(data, dict) and data.get("event") == "error":
                print("AUDIO ❌", data)

    if not AUDIO_INGEST_TOKEN and REGISTER_SOURCE:
        token = await _ensure_audio_token()
    else:
        token = AUDIO_INGEST_TOKEN
    if not token:
        raise RuntimeError("Missing audio_ingest_token. Set MEETMATE_AUDIO_INGEST_TOKEN or enable MEETMATE_REGISTER_SOURCE=1.")

    url = f"{ws_base}/api/v1/ws/audio/{SESSION_ID}?token={token}"

    async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5, max_size=16 * 1024 * 1024) as ws:
        print("✅ Connected:", url)

        # Server sends a connected envelope first
        try:
            hello = await asyncio.wait_for(ws.recv(), timeout=2)
            print("AUDIO ⬅️", hello)
        except asyncio.TimeoutError:
            pass

        start_msg = {
            "type": "start",
            "platform": "dev_wav",
            "platform_meeting_ref": f"wav:{os.path.basename(WAV_PATH)}",
            "audio": {"codec": "PCM_S16LE", "sample_rate_hz": TARGET_SR, "channels": 1},
            "language_code": LANGUAGE_CODE,
            "frame_ms": nonlocal_frame_ms["value"],
            "stream_id": "aud_01",
            "client_ts_ms": int(time.time() * 1000),
        }
        await ws.send(json.dumps(start_msg))
        ack = await asyncio.wait_for(ws.recv(), timeout=5)
        print("AUDIO ⬅️", ack)

        recv_task = asyncio.create_task(recv_audio_events(ws))

        with wave.open(WAV_PATH, "rb") as wf:
            in_channels = wf.getnchannels()
            in_width = wf.getsampwidth()
            in_rate = wf.getframerate()
            print(f"WAV info: channels={in_channels} width={in_width} rate={in_rate}Hz")

            state = None
            out_buf = b""
            sent_frames = 0

            while True:
                # Read ~1s from source to reduce overhead, then chunk to FRAME_MS
                raw = wf.readframes(in_rate)
                if not raw:
                    break
                pcm = _to_pcm16_mono(raw, in_width=in_width, in_channels=in_channels)
                if in_rate != TARGET_SR:
                    converted, state = audioop.ratecv(pcm, 2, 1, in_rate, TARGET_SR, state)
                else:
                    converted = pcm
                out_buf += converted

                while True:
                    frame_ms = int(nonlocal_frame_ms["value"])
                    bytes_per_frame = int(TARGET_SR * 2 * 1 * frame_ms / 1000)
                    if len(out_buf) < bytes_per_frame:
                        break
                    frame = out_buf[:bytes_per_frame]
                    out_buf = out_buf[bytes_per_frame:]

                    await ws.send(frame)
                    sent_frames += 1
                    await asyncio.sleep(frame_ms / 1000)

        await asyncio.sleep(POST_STREAM_WAIT_SEC)
        stop.set()
        recv_task.cancel()


async def main():
    ws_base = _ws_base_from_http(HTTP_BASE).rstrip("/")
    print("HTTP_BASE:", HTTP_BASE)
    print("WS_BASE:", ws_base)
    print("SESSION_ID:", SESSION_ID)
    print("WAV_PATH:", os.path.abspath(WAV_PATH))
    if not os.path.exists(WAV_PATH):
        raise FileNotFoundError(f"WAV not found: {WAV_PATH}")

    if CREATE_SESSION:
        session_resp = await _ensure_session()
        print("✅ Session created:", session_resp.get("session_id"))
        print("  audio_ws_url:", session_resp.get("audio_ws_url"))
        print("  frontend_ws_url:", session_resp.get("frontend_ws_url"))
        print("  transcript_test_ws_url:", session_resp.get("transcript_test_ws_url"))
    else:
        print("⚠️ Skipping session creation (MEETMATE_CREATE_SESSION=0). Make sure session exists.")

    stop = asyncio.Event()
    await asyncio.gather(_listen_frontend(stop, ws_base), _stream_audio(stop, ws_base))


if __name__ == "__main__":
    asyncio.run(main())
