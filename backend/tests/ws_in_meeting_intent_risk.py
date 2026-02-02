"""
Quick WS test for intent: RISK_STATEMENT.

Usage:
  python vnpt_ai_hackathon/backend/tests/ws_in_meeting_intent_risk.py

Env (optional):
  MEETMATE_HTTP_BASE=https://vnpt-ai-hackathon-meetmate.onrender.com
  MEETMATE_WS_BASE=wss://vnpt-ai-hackathon-meetmate.onrender.com
  MEETMATE_SESSION_ID=<uuid>
  MEETMATE_CREATE_SESSION=1
  MEETMATE_OVERALL_TIMEOUT_SEC=30
  MEETMATE_CHUNK_TEXT="risk ..."
"""

import asyncio
import json
import os
import uuid
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    import websockets
except Exception as exc:  # pragma: no cover - manual script
    raise SystemExit("Missing dependency: pip install websockets") from exc


HTTP_BASE = os.getenv("MEETMATE_HTTP_BASE", "https://vnpt-ai-hackathon-meetmate.onrender.com").strip()
if HTTP_BASE and "://" not in HTTP_BASE and not HTTP_BASE.startswith(("ws://", "wss://")):
    HTTP_BASE = "https://" + HTTP_BASE
HTTP_BASE = HTTP_BASE.rstrip("/")
WS_BASE = os.getenv("MEETMATE_WS_BASE", "").strip()
SESSION_ID = os.getenv("MEETMATE_SESSION_ID", "").strip() or str(uuid.uuid4())
CREATE_SESSION = os.getenv("MEETMATE_CREATE_SESSION", "1").lower() not in ("0", "false", "no")
OVERALL_TIMEOUT_SEC = float(os.getenv("MEETMATE_OVERALL_TIMEOUT_SEC", "30"))

EXPECTED_INTENT = "RISK_STATEMENT"
DEFAULT_TEXT = "Main risk is security issues; risk level medium. Need mitigation plan."
CHUNK_TEXT = os.getenv("MEETMATE_CHUNK_TEXT", DEFAULT_TEXT)


def _ws_base_from_http(http_base: str) -> str:
    if http_base.startswith("https://"):
        return "wss://" + http_base[len("https://") :]
    if http_base.startswith("http://"):
        return "ws://" + http_base[len("http://") :]
    if http_base.startswith("ws://") or http_base.startswith("wss://"):
        return http_base
    return "ws://" + http_base


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body)
    except (URLError, OSError) as exc:
        raise SystemExit(
            f"Cannot reach backend at {HTTP_BASE}. Start the server or set MEETMATE_HTTP_BASE. Error: {exc}"
        ) from exc


def _ensure_session() -> str:
    global SESSION_ID
    if SESSION_ID and not CREATE_SESSION:
        return SESSION_ID
    if CREATE_SESSION:
        payload = {
            "session_id": SESSION_ID,
            "language_code": "vi-VN",
            "target_sample_rate_hz": 16000,
            "audio_encoding": "PCM_S16LE",
            "channels": 1,
            "realtime": True,
            "interim_results": True,
            "enable_word_time_offsets": True,
        }
        resp = _post_json(f"{HTTP_BASE}/api/v1/sessions", payload)
        SESSION_ID = resp["session_id"]
        return SESSION_ID
    raise SystemExit("Set MEETMATE_SESSION_ID or enable MEETMATE_CREATE_SESSION=1.")


async def _listen_frontend(stop: asyncio.Event) -> None:
    url = f"{WS_BASE}/api/v1/ws/frontend/{SESSION_ID}"
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as ws:
        while not stop.is_set():
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=1)
            except asyncio.TimeoutError:
                continue
            data = json.loads(msg)
            if data.get("event") != "state":
                continue
            payload = data.get("payload") or {}
            intent = payload.get("semantic_intent_label")
            print(
                "STATE intent=",
                intent,
                "topic=",
                payload.get("current_topic_id"),
                "recap=",
                payload.get("live_recap"),
            )
            if intent == EXPECTED_INTENT:
                stop.set()


async def _send_transcript(stop: asyncio.Event) -> None:
    url = f"{WS_BASE}/api/v1/ws/in-meeting/{SESSION_ID}"
    async with websockets.connect(url, ping_interval=20, ping_timeout=20, close_timeout=5) as ws:
        try:
            hello = await asyncio.wait_for(ws.recv(), timeout=2)
            print("WS connected:", hello)
        except asyncio.TimeoutError:
            pass

        payload = {
            "meeting_id": SESSION_ID,
            "chunk": CHUNK_TEXT,
            "speaker": "SPEAKER_01",
            "time_start": 0.0,
            "time_end": 12.0,
            "is_final": True,
            "confidence": 0.9,
            "lang": "vi",
        }
        await ws.send(json.dumps(payload))
        try:
            ack = await asyncio.wait_for(ws.recv(), timeout=3)
            print("ACK:", ack)
        except asyncio.TimeoutError:
            print("WARN: no ingest_ack")

        while not stop.is_set():
            await asyncio.sleep(0.2)


async def _stop_after(stop: asyncio.Event, timeout_sec: float) -> None:
    await asyncio.sleep(timeout_sec)
    if not stop.is_set():
        print(f"Timeout after {timeout_sec:.0f}s without intent {EXPECTED_INTENT}.")
        stop.set()


async def main() -> None:
    global WS_BASE
    session_id = _ensure_session()
    if not WS_BASE:
        WS_BASE = _ws_base_from_http(HTTP_BASE).rstrip("/")
    print("HTTP_BASE:", HTTP_BASE)
    print("WS_BASE:", WS_BASE)
    print("SESSION_ID:", session_id)
    print("EXPECTED_INTENT:", EXPECTED_INTENT)

    stop = asyncio.Event()
    await asyncio.gather(
        _listen_frontend(stop),
        _send_transcript(stop),
        _stop_after(stop, OVERALL_TIMEOUT_SEC),
    )


if __name__ == "__main__":
    asyncio.run(main())
