import asyncio
import inspect
import json
import os
import time

import websockets

HTTP_BASE = os.getenv("MEETMATE_HTTP_BASE", "http://localhost:8000").rstrip("/")
SESSION_ID = os.getenv("MEETMATE_SESSION_ID", "c0000002-0000-0000-0000-000000000002")

if HTTP_BASE.startswith("https://"):
    WS_BASE = "wss://" + HTTP_BASE[len("https://") :]
elif HTTP_BASE.startswith("http://"):
    WS_BASE = "ws://" + HTTP_BASE[len("http://") :]
else:
    WS_BASE = HTTP_BASE

WS_URL = f"{WS_BASE}/api/v1/ws/in-meeting/{SESSION_ID}"
TOKEN = None  # "Bearer xxx" nếu cần (không bắt buộc cho PoC)


async def run():
    headers = {}
    if TOKEN:
        headers["Authorization"] = TOKEN

    connect_kwargs = dict(
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
        max_size=4 * 1024 * 1024,
    )

    sig = inspect.signature(websockets.connect)
    if headers:
        if "additional_headers" in sig.parameters:
            connect_kwargs["additional_headers"] = headers
        elif "extra_headers" in sig.parameters:
            connect_kwargs["extra_headers"] = headers
        else:
            raise RuntimeError(f"websockets.connect không hỗ trợ headers params. Signature: {sig}")

    async with websockets.connect(WS_URL, **connect_kwargs) as ws:
        print("✅ Connected:", WS_URL)

        # Server sends a "connected" envelope first
        try:
            hello = await asyncio.wait_for(ws.recv(), timeout=3)
            print("⬅️ recv:", hello)
        except asyncio.TimeoutError:
            pass

        msg1 = {
            "meeting_id": SESSION_ID,
            "chunk": "xin chào anh chị, hôm nay mình",
            "speaker": "SPEAKER_01",
            "time_start": 0.0,
            "time_end": 1.5,
            "is_final": False,
            "confidence": 0.82,
            "lang": "vi",
            "question": False,
        }
        await ws.send(json.dumps(msg1, ensure_ascii=False))
        print("➡️ sent:", msg1)

        resp1 = await asyncio.wait_for(ws.recv(), timeout=5)
        print("⬅️ recv:", resp1)

        msg2 = dict(msg1)
        msg2["time_start"] = 1.5
        msg2["time_end"] = 3.2
        msg2["chunk"] = "đi qua checklist realtime integration"
        msg2["is_final"] = True
        await ws.send(json.dumps(msg2, ensure_ascii=False))
        print("➡️ sent:", msg2)

        resp2 = await asyncio.wait_for(ws.recv(), timeout=5)
        print("⬅️ recv:", resp2)

        # Keep listening (ACK/error) for a short time
        start = time.time()
        while time.time() - start < 5:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=1)
                print("⬅️ recv:", resp)
            except asyncio.TimeoutError:
                pass


if __name__ == "__main__":
    asyncio.run(run())
