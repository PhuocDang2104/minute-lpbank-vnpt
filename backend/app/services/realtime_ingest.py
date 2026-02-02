from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError

from app.schemas.realtime import TranscriptIngestPayload
from app.services.realtime_bus import session_bus
from app.services.realtime_session_store import session_store


def _validate_required(payload: TranscriptIngestPayload) -> None:
    if not payload.chunk or not payload.chunk.strip():
        raise ValueError("chunk must be non-empty")
    if payload.time_end < payload.time_start:
        raise ValueError("time_end must be >= time_start")


async def ingestTranscript(session_id: str, payload: Dict[str, Any], source: str) -> int:
    """
    SSOT for transcript ingestion (SmartVoice STT or dev/test WS).

    MUST:
    - validate required fields
    - allocate seq (monotonic per session)
    - publish transcript_event onto the session bus
    - return seq
    """
    try:
        seg = TranscriptIngestPayload.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    _validate_required(seg)

    session_store.ensure(session_id)
    transcript_window = session_store.append_transcript(session_id, seg.chunk, max_chars=4000)

    event_payload: Dict[str, Any] = {
        "meeting_id": seg.meeting_id,
        "chunk": seg.chunk,
        "speaker": seg.speaker,
        "time_start": seg.time_start,
        "time_end": seg.time_end,
        "is_final": seg.is_final,
        "confidence": seg.confidence,
        "lang": seg.lang,
        # internal-only helpers (frontend distributor may strip)
        "question": seg.question,
        "transcript_window": transcript_window,
        "source": source,
    }

    envelope = await session_bus.publish(
        session_id,
        {
            "event": "transcript_event",
            "payload": event_payload,
        },
    )
    seq = int(envelope.get("seq") or 0)

    return seq


async def publish_state(session_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    envelope = await session_bus.publish(
        session_id,
        {
            "event": "state",
            "payload": state,
        },
    )
    return envelope

