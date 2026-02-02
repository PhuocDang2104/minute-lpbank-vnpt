import asyncio
import json
import os
import time
import uuid
import wave
import warnings

# Python 3.11+ emits DeprecationWarning for `audioop` with stacklevel=2, so the
# warning is attributed to this script (module=__main__). Filter by message.
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*audioop.*")

import audioop
import httpx
import websockets

"""
Test WS raw audio ingress (MeetMate).

What this script verifies:
- [OK] WS connects and server returns `audio_start_ack` (API accepted audio start + format)
- [OK] Audio frames are streamed without WS disconnect
- [WARN] If SmartVoice is not configured/working, server may emit `smartvoice_error` and close the WS.

Default WAV path is the one you provided:
  C:\\Users\\ADMIN\\Desktop\\vnpt_meetmate\\vnpt_ai_hackathon\\backend\\tests\\resources\\eLabs-1.wav
The file is 44.1kHz mono 16-bit, so we resample to 16kHz before streaming.
"""

DEFAULT_WAV_PATH = (
    r"C:\Users\ADMIN\Desktop\vnpt_meetmate\vnpt_ai_hackathon\backend\tests\resources\eLabs-1.wav"
)

HTTP_BASE = os.getenv("MEETMATE_HTTP_BASE", "https://vnpt-ai-hackathon-meetmate.onrender.com").strip()
if HTTP_BASE and "://" not in HTTP_BASE and not HTTP_BASE.startswith(("ws://", "wss://")):
    HTTP_BASE = "https://" + HTTP_BASE
HTTP_BASE = HTTP_BASE.rstrip("/")
SESSION_ID = os.getenv("MEETMATE_SESSION_ID", "").strip() or str(uuid.uuid4())
WAV_PATH = os.getenv("MEETMATE_WAV_PATH", DEFAULT_WAV_PATH)
LANGUAGE_CODE = os.getenv("MEETMATE_LANGUAGE_CODE", "vi-VN")
FRAME_MS = int(os.getenv("MEETMATE_FRAME_MS", "250"))
TARGET_SR = int(os.getenv("MEETMATE_TARGET_SR", "16000"))

ACK_TIMEOUT_SEC = float(os.getenv("MEETMATE_ACK_TIMEOUT_SEC", "5.0"))
INGEST_OK_TIMEOUT_SEC = float(os.getenv("MEETMATE_INGEST_OK_TIMEOUT_SEC", "3.0"))

# By default this script only tests audio ingest (no SmartVoice).
# Set MEETMATE_STT=1 if you want to enable STT on the backend.
STT_PARAM = "1" if os.getenv("MEETMATE_STT", "0").strip() in ("1", "true", "True", "on") else "0"


def _ws_base_from_http(http_base: str) -> str:
    if http_base.startswith("https://"):
        return "wss://" + http_base[len("https://") :]
    if http_base.startswith("http://"):
        return "ws://" + http_base[len("http://") :]
    if http_base.startswith("ws://") or http_base.startswith("wss://"):
        return http_base
    return "ws://" + http_base


async def _print_openapi_debug() -> None:
    url = f"{HTTP_BASE}/openapi.json"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"[INFO] openapi.json not available ({resp.status_code}): {url}")
                return
            data = resp.json()
            paths = sorted((data.get("paths") or {}).keys())
            session_like = [p for p in paths if "session" in p.lower()]
            ws_like = [p for p in paths if "ws" in p.lower()]
            print("[INFO] OpenAPI quick check:")
            print("  - has /api/v1/sessions:", "/api/v1/sessions" in paths)
            if session_like:
                print("  - session-like paths (first 10):")
                for p in session_like[:10]:
                    print("    ", p)
            if ws_like:
                print("  - ws-like paths (first 10):")
                for p in ws_like[:10]:
                    print("    ", p)
    except Exception as exc:
        print(f"[INFO] Failed to fetch OpenAPI for debug: {exc}")


async def _create_session() -> dict:
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


async def _register_source_token() -> str:
    url = f"{HTTP_BASE}/api/v1/sessions/{SESSION_ID}/sources"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url)
        resp.raise_for_status()
        return resp.json()["audio_ingest_token"]


def _resample_to_16k_mono_s16le(wf: wave.Wave_read, frame_ms: int) -> bytes:
    in_channels = wf.getnchannels()
    in_width = wf.getsampwidth()
    in_rate = wf.getframerate()

    state = None
    out = b""

    # Read chunks from file, resample, and return a contiguous PCM buffer.
    # We keep it simple (file is short) for test usage.
    while True:
        raw = wf.readframes(in_rate)  # ~1s
        if not raw:
            break

        pcm = raw
        if in_width != 2:
            pcm = audioop.lin2lin(pcm, in_width, 2)
            in_width = 2
        if in_channels != 1:
            pcm = audioop.tomono(pcm, in_width, 0.5, 0.5)

        if in_rate != TARGET_SR:
            converted, state = audioop.ratecv(pcm, 2, 1, in_rate, TARGET_SR, state)
        else:
            converted = pcm
        out += converted

    return out


async def main() -> int:
    print("== MeetMate WS Audio Ingest Test ==")
    print("HTTP_BASE:", HTTP_BASE)
    print("SESSION_ID:", SESSION_ID)
    print("WAV_PATH:", WAV_PATH)

    if not os.path.exists(WAV_PATH):
        print(f"[ERR] WAV file not found: {WAV_PATH}")
        return 1

    # 1) Create session
    try:
        sess = await _create_session()
        print("[OK] Session created:", sess.get("session_id"))
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            print(f"[ERR] Backend {HTTP_BASE} does not expose realtime endpoint `POST /api/v1/sessions` (404).")
            print("      It looks like your Render deployment is outdated; redeploy the backend before testing WS audio ingest.")
            await _print_openapi_debug()
        else:
            print("[ERR] Failed to create session:", exc)
        return 1
    except Exception as exc:
        print("[ERR] Failed to create session:", exc)
        return 1

    # 2) Register source -> token
    try:
        token = await _register_source_token()
        print("[OK] Got audio_ingest_token (len={} chars)".format(len(token)))
    except Exception as exc:
        print("[ERR] Failed to register source token:", exc)
        return 1

    ws_base = _ws_base_from_http(HTTP_BASE).rstrip("/")
    audio_ws_url = f"{ws_base}/api/v1/ws/audio/{SESSION_ID}?token={token}&stt={STT_PARAM}"

    # 3) Connect WS + start
    ack_ok = False
    ingest_ok = asyncio.Event()
    server_error = None
    throttle_events = 0
    stt_disabled_notice = False

    try:
        async with websockets.connect(
            audio_ws_url,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=5,
            max_size=16 * 1024 * 1024,
        ) as ws:
            print("[OK] WS connected:", audio_ws_url)

            # Consume optional connected message
            try:
                hello = await asyncio.wait_for(ws.recv(), timeout=2)
                print("<-", hello)
            except asyncio.TimeoutError:
                pass

            start_msg = {
                "type": "start",
                "platform": "dev_wav",
                "platform_meeting_ref": f"wav:{os.path.basename(WAV_PATH)}",
                "audio": {"codec": "PCM_S16LE", "sample_rate_hz": TARGET_SR, "channels": 1},
                "language_code": LANGUAGE_CODE,
                "frame_ms": FRAME_MS,
                "stream_id": "aud_01",
                "client_ts_ms": int(time.time() * 1000),
            }
            await ws.send(json.dumps(start_msg))

            # Wait for audio_start_ack
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=ACK_TIMEOUT_SEC)
            except asyncio.TimeoutError:
                print("[ERR] No audio_start_ack within timeout ({}s).".format(ACK_TIMEOUT_SEC))
                return 1

            print("<-", msg)
            if isinstance(msg, str):
                try:
                    data = json.loads(msg)
                except Exception:
                    data = {}
                if data.get("event") == "audio_start_ack":
                    ack_ok = True
                    if data.get("stt_enabled") is False:
                        stt_disabled_notice = True
                    print("[OK] audio_start_ack -> API accepted start + audio format.")
                elif data.get("event") == "error":
                    print("[ERR] API returned error right after start:", data)
                    return 1

            if not ack_ok:
                print("[ERR] Did not receive a valid audio_start_ack.")
                return 1

            async def recv_events():
                nonlocal server_error, throttle_events, stt_disabled_notice
                while True:
                    try:
                        raw = await ws.recv()
                    except Exception:
                        return
                    if not isinstance(raw, str):
                        continue
                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue
                    if not isinstance(data, dict):
                        continue

                    event = data.get("event")
                    if event == "audio_ingest_ok":
                        if not ingest_ok.is_set():
                            ingest_ok.set()
                            print("[OK] audio_ingest_ok:", data)
                    elif event == "stt_disabled":
                        stt_disabled_notice = True
                        print("[INFO] stt_disabled:", data)
                    elif event == "throttle":
                        throttle_events += 1
                        print("[WARN] throttle:", data)
                    elif event == "error":
                        server_error = data
                        print("[ERR] server error:", data)
                        ingest_ok.set()
                        return

            recv_task = asyncio.create_task(recv_events())

            # 4) Stream WAV as PCM16 mono 16kHz frames
            with wave.open(WAV_PATH, "rb") as wf:
                print(
                    "WAV info: channels={}, width={}, rate={}Hz, frames={}".format(
                        wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
                    )
                )
                pcm = _resample_to_16k_mono_s16le(wf, FRAME_MS)

            bytes_per_frame = int(TARGET_SR * 2 * 1 * FRAME_MS / 1000)
            total_frames = (len(pcm) + bytes_per_frame - 1) // bytes_per_frame
            print(f"Streaming: target_sr={TARGET_SR}, frame_ms={FRAME_MS}, frames={total_frames}")

            sent = 0
            for i in range(total_frames):
                if server_error:
                    break
                chunk = pcm[i * bytes_per_frame : (i + 1) * bytes_per_frame]
                if not chunk:
                    break
                await ws.send(chunk)
                sent += 1
                if sent == 1:
                    try:
                        await asyncio.wait_for(ingest_ok.wait(), timeout=INGEST_OK_TIMEOUT_SEC)
                    except asyncio.TimeoutError:
                        print("[ERR] Did not receive audio_ingest_ok (server did not confirm first frame).")
                        recv_task.cancel()
                        return 1
                if sent % 10 == 0:
                    print(f"-> sent frames: {sent}/{total_frames}")
                await asyncio.sleep(FRAME_MS / 1000)

            # Signal stop (optional)
            try:
                await ws.send(json.dumps({"type": "stop"}))
            except Exception:
                pass

            await asyncio.sleep(1.0)
            recv_task.cancel()

            if server_error:
                print("[ERR] FAIL: server reported error while streaming.")
                return 1

            print(f"[OK] OK: streamed {sent} frames, throttle_events={throttle_events}.")
            if stt_disabled_notice:
                print("[INFO] Note: STT is disabled (ingest-only test).")
            print("[OK] Conclusion: API received audio (audio_start_ack + audio_ingest_ok).")
            return 0

    except Exception as exc:
        print("[ERR] WS connection/streaming error:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
