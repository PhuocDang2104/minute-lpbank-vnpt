from typing import Any, Dict, List

from fastapi import APIRouter

from app.services.realtime_session_store import session_store
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/diarization/{session_id}")
async def ingest_diarization(session_id: str, payload: Dict[str, Any]):
    session = session_store.get(session_id)
    if not session:
        return {"status": "error", "reason": "session_not_found"}

    segments: List[Dict[str, Any]] = payload.get("segments") or []
    if not segments:
        return {"status": "ok"}

    stream_state = session.stream_state
    for seg in segments:
        try:
            speaker = seg["speaker"]
            start = float(seg["start"])
            end = float(seg["end"])
        except (KeyError, TypeError, ValueError):
            continue
        confidence = seg.get("confidence", 1.0)
        stream_state.speaker_segments.append(
            {
                "speaker": speaker,
                "start": start,
                "end": end,
                "confidence": float(confidence if confidence is not None else 1.0),
            }
        )

    logger.info("diarization_ingested session_id=%s segments=%s", session_id, len(stream_state.speaker_segments))
    return {"status": "ok"}


@router.get("/diarization/{session_id}")
async def get_diarization(session_id: str):
    session = session_store.get(session_id)
    if not session:
        return {"status": "error", "reason": "session_not_found"}
    stream_state = session.stream_state
    segments = sorted(stream_state.speaker_segments, key=lambda s: s.get("start", 0.0))
    return {"status": "ok", "segments": segments}
