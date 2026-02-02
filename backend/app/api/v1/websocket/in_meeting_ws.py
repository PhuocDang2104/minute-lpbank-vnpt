import asyncio
import inspect
import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.realtime_security import verify_audio_ingest_token
from app.llm.chains.in_meeting_chain import summarize_and_classify
from app.schemas.realtime import AudioStartMessage
from app.services.realtime_bus import session_bus
from app.services.realtime_ingest import ingestTranscript
from app.services.realtime_session_store import FinalTranscriptChunk, session_store
from app.services.smartvoice_streaming import SmartVoiceStreamingConfig, is_smartvoice_configured, stream_recognize

router = APIRouter()
stream_workers: Dict[str, asyncio.Task] = {}
logger = logging.getLogger(__name__)

RECAP_WINDOW_SEC = 60.0
ROLLING_RETENTION_SEC = 120.0
RECAP_TICK_SEC = 30.0
RECAP_WINDOW_MIN = 30.0


class _AudioClock:
    def __init__(self, sample_rate_hz: int, channels: int, bytes_per_sample: int = 2) -> None:
        self.sample_rate_hz = sample_rate_hz
        self.channels = channels
        self.bytes_per_sample = bytes_per_sample
        self.total_samples = 0

    def advance(self, byte_len: int) -> None:
        if byte_len <= 0 or self.sample_rate_hz <= 0 or self.channels <= 0:
            return
        samples = byte_len // (self.bytes_per_sample * self.channels)
        self.total_samples += max(0, int(samples))

    def now_s(self) -> float:
        if self.sample_rate_hz <= 0:
            return 0.0
        return float(self.total_samples) / float(self.sample_rate_hz)


def _format_chunk_line(chunk: FinalTranscriptChunk) -> str:
    return f"[{chunk.speaker} {chunk.time_start:.2f}-{chunk.time_end:.2f}] {chunk.text}".strip()


def _build_window_text(chunks: List[FinalTranscriptChunk]) -> str:
    return "\n".join(_format_chunk_line(chunk) for chunk in chunks if chunk.text)


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)



def _match_speaker_by_time(segments, t_start: float, t_end: float):
    best = None
    best_overlap = 0.0

    for seg in segments:
        overlap = min(t_end, seg["end"]) - max(t_start, seg["start"])
        if overlap > best_overlap:
            best_overlap = overlap
            best = seg

    if best_overlap <= 0:
        return None

    return best

def _compute_tick_anchor(stream_state) -> float:
    anchor = stream_state.max_seen_time_end or 0.0
    if stream_state.last_partial_chunk:
        anchor = max(anchor, stream_state.last_partial_chunk.time_end)
    return anchor



def _prune_stream_state(stream_state) -> None:
    cutoff = stream_state.max_seen_time_end - ROLLING_RETENTION_SEC
    if cutoff <= 0:
        return
    kept = [chunk for chunk in stream_state.rolling_window if chunk.time_end >= cutoff]
    stream_state.rolling_window.clear()
    stream_state.rolling_window.extend(kept)
    keep_seqs = {chunk.seq for chunk in kept}
    for seq in list(stream_state.final_by_seq.keys()):
        if seq not in keep_seqs:
            stream_state.final_by_seq.pop(seq, None)


def _append_final_chunk(stream_state, chunk: FinalTranscriptChunk, now: float) -> None:
    stream_state.final_stream.append(chunk)
    stream_state.final_by_seq[chunk.seq] = chunk
    stream_state.rolling_window.append(chunk)
    stream_state.last_final_seq = max(stream_state.last_final_seq, chunk.seq)
    if chunk.time_end > stream_state.max_seen_time_end:
        stream_state.max_seen_time_end = chunk.time_end
    if stream_state.last_recap_tick_at <= 0.0:
        stream_state.last_recap_tick_at = now
    _prune_stream_state(stream_state)


def _update_last_transcript(stream_state, chunk: FinalTranscriptChunk, seq: int, is_final: bool, now: float) -> None:
    stream_state.last_transcript_seq = max(stream_state.last_transcript_seq, seq)
    stream_state.last_transcript_chunk = chunk
    stream_state.last_transcript_is_final = is_final
    if not is_final:
        stream_state.last_partial_seq = seq
        stream_state.last_partial_chunk = chunk
    if stream_state.last_recap_tick_at <= 0.0:
        stream_state.last_recap_tick_at = now


def _select_window_chunks(stream_state, window_sec: float, include_partial: bool = False) -> List[FinalTranscriptChunk]:
    if not stream_state.rolling_window and not (include_partial and stream_state.last_partial_chunk):
        return []
    anchor = stream_state.max_seen_time_end or 0.0
    if stream_state.rolling_window:
        anchor = max(anchor, stream_state.rolling_window[-1].time_end)
    if include_partial and stream_state.last_partial_chunk:
        anchor = max(anchor, stream_state.last_partial_chunk.time_end)
    cutoff = anchor - window_sec
    chunks = [chunk for chunk in stream_state.rolling_window if chunk.time_end >= cutoff]
    if include_partial and stream_state.last_partial_chunk:
        partial = stream_state.last_partial_chunk
        if partial.time_end >= cutoff:
            if not chunks or (
                partial.time_end != chunks[-1].time_end
                or partial.text != chunks[-1].text
                or partial.speaker != chunks[-1].speaker
            ):
                chunks.append(partial)
    chunks.sort(key=lambda chunk: (chunk.time_end, chunk.seq))
    return chunks


def _should_recap_tick(stream_state, now: float) -> bool:
    if stream_state.last_transcript_seq <= stream_state.recap_cursor_seq:
        return False
    anchor = _compute_tick_anchor(stream_state)
    return (anchor - stream_state.last_recap_tick_anchor) >= RECAP_TICK_SEC


def _run_recap_tick(session_id: str, stream_state, now: float) -> Optional[Dict[str, Any]]:
    cursor_before = stream_state.recap_cursor_seq
    anchor = _compute_tick_anchor(stream_state)
    include_partial = stream_state.last_partial_chunk is not None and stream_state.last_partial_seq >= stream_state.last_final_seq
    window_chunks = _select_window_chunks(stream_state, RECAP_WINDOW_SEC, include_partial=include_partial)
    window_text = _build_window_text(window_chunks)
    window_start = window_chunks[0].time_start if window_chunks else 0.0
    window_end = window_chunks[-1].time_end if window_chunks else 0.0
    window_duration = max(0.0, window_end - window_start)
    if not window_text or window_duration < RECAP_WINDOW_MIN:
        stream_state.recap_cursor_seq = stream_state.last_transcript_seq
        stream_state.last_recap_tick_at = now
        stream_state.last_recap_tick_anchor = anchor
        logger.info(
            "recap_tick_skip session_id=%s cursor=%s->%s window=%.2f-%.2f duration=%.2fs anchor=%.2f",
            session_id,
            cursor_before,
            stream_state.recap_cursor_seq,
            window_start,
            window_end,
            window_duration,
            anchor,
        )
        return None

    meta = {
        "current_topic_id": stream_state.current_topic_id,
        "current_topic": stream_state.last_topic_payload,
        "window_start": window_start,
        "window_end": window_end,
    }
    llm_start = time.time()
    result = summarize_and_classify(window_text, meta=meta)
    llm_latency_ms = int((time.time() - llm_start) * 1000)
    parse_ok = bool(meta.get("parse_ok"))

    recap = result.get("recap") or ""
    topic_payload = result.get("topic") or {}
    intent_payload = result.get("intent") or {}

    topic_id = topic_payload.get("topic_id") if isinstance(topic_payload.get("topic_id"), str) else None
    if not topic_id:
        topic_id = stream_state.current_topic_id or "T0"
    topic_title = topic_payload.get("title") if isinstance(topic_payload.get("title"), str) else "General"
    topic_start = _coerce_float(topic_payload.get("start_t"), window_start)
    topic_end = _coerce_float(topic_payload.get("end_t"), window_end)
    if topic_end < topic_start:
        topic_end = topic_start

    if topic_payload.get("new_topic") or not stream_state.topic_segments:
        stream_state.topic_segments.append({
            "topic_id": topic_id,
            "title": topic_title,
            "start_t": topic_start,
            "end_t": topic_end,
        })
    stream_state.current_topic_id = topic_id
    stream_state.last_topic_payload = topic_payload
    stream_state.last_intent_payload = intent_payload
    stream_state.semantic_intent_label = intent_payload.get("label") or "NO_INTENT"
    stream_state.semantic_intent_slots = intent_payload.get("slots") or {}
    stream_state.last_live_recap = recap
    stream_state.last_recap = recap

    stream_state.recap_cursor_seq = stream_state.last_transcript_seq
    stream_state.last_recap_tick_at = now
    stream_state.last_recap_tick_anchor = anchor
    _prune_stream_state(stream_state)

    logger.info(
        "recap_tick session_id=%s cursor=%s->%s window=%.2f-%.2f duration=%.2fs anchor=%.2f chunks=%s llm_ms=%s parse_ok=%s include_partial=%s",
        session_id,
        cursor_before,
        stream_state.recap_cursor_seq,
        window_start,
        window_end,
        window_duration,
        anchor,
        len(window_chunks),
        llm_latency_ms,
        parse_ok,
        include_partial,
    )

    return {
        "meeting_id": session_id,
        "stage": "in",
        "intent": "tick",
        "sla": "near_realtime",
        "live_recap": recap,
        "recap": recap,
        "topic": topic_payload,
        "intent_payload": intent_payload,
        "transcript_window": window_text,
        "semantic_intent_label": stream_state.semantic_intent_label,
        "semantic_intent_slots": stream_state.semantic_intent_slots,
        "topic_segments": stream_state.topic_segments,
        "current_topic_id": stream_state.current_topic_id,
        # Deprecated: ADR extraction removed; keep empty lists for compatibility.
        "actions": stream_state.actions,
        "decisions": stream_state.decisions,
        "risks": stream_state.risks,
        # Deprecated in realtime tick; kept for backward-compatible payload shape.
        "tool_suggestions": [],
        "debug_info": {
            "recap_cursor_before": cursor_before,
            "recap_cursor_seq": stream_state.recap_cursor_seq,
            "window_sec": RECAP_WINDOW_SEC,
            "window_start": window_start,
            "window_end": window_end,
            "window_duration": window_duration,
            "window_chunks": len(window_chunks),
            "include_partial": include_partial,
            "llm_latency_ms": llm_latency_ms,
            "parse_ok": parse_ok,
            "raw_len": meta.get("raw_len"),
            "last_recap_tick_anchor": stream_state.last_recap_tick_anchor,
            "last_final_seq": stream_state.last_final_seq,
            "last_transcript_seq": stream_state.last_transcript_seq,
        },
    }


async def _publish_state_event(session_id: str, state: Dict[str, Any]) -> None:
    version = session_store.next_state_version(session_id)
    await session_bus.publish(
        session_id,
        {
            "event": "state",
            "version": version,
            "payload": state,
        },
    )


async def _stream_consumer(session_id: str, queue: asyncio.Queue) -> None:
    session = session_store.ensure(session_id)
    stream_state = session.stream_state
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=900)
            except asyncio.TimeoutError:
                break
            if event.get("event") != "transcript_event":
                continue
            payload = event.get("payload") or {}
            is_final = bool(payload.get("is_final", True))

            try:
                seq = int(event.get("seq") or 0)
            except (TypeError, ValueError):
                seq = 0

            confidence = payload.get("confidence")
            time_start = float(payload.get("time_start") or 0.0)
            time_end = float(payload.get("time_end") or 0.0)
            speaker = payload.get("speaker") or "SPEAKER_01"

            chunk = FinalTranscriptChunk(
                seq=seq,
                time_start=time_start,
                time_end=time_end,
                speaker=speaker,
                lang=payload.get("lang") or "vi",
                confidence=float(1.0 if confidence is None else confidence),
                text=payload.get("chunk") or payload.get("text") or "",
            )
            now = time.time()
            _update_last_transcript(stream_state, chunk, seq, is_final, now)
            if is_final:
                _append_final_chunk(stream_state, chunk, now)

            recap_due = _should_recap_tick(stream_state, now)

            if recap_due:
                try:
                    recap_state = _run_recap_tick(session_id, stream_state, now)
                    if recap_state:
                        await _publish_state_event(session_id, recap_state)
                except Exception:
                    pass
    except asyncio.CancelledError:
        pass
    finally:
        session_bus.unsubscribe(session_id, queue)
        stream_workers.pop(session_id, None)


def _ensure_stream_worker(session_id: str) -> None:
    task = stream_workers.get(session_id)
    if task and not task.done():
        return
    queue = session_bus.subscribe(session_id)
    stream_workers[session_id] = asyncio.create_task(_stream_consumer(session_id, queue))


async def _safe_send_json(websocket: WebSocket, lock: asyncio.Lock, payload: Dict[str, Any]) -> None:
    async with lock:
        await websocket.send_json(payload)


async def _smartvoice_to_bus(
    session_id: str,
    audio_queue: "asyncio.Queue[Optional[bytes]]",
    cfg: SmartVoiceStreamingConfig,
    audio_clock: _AudioClock,
    websocket: WebSocket,
    send_lock: asyncio.Lock,
) -> None:
    last_end = 0.0
    try:
        stream_iter = stream_recognize(audio_queue, cfg)
        if inspect.isawaitable(stream_iter):
            stream_iter = await stream_iter
        if not hasattr(stream_iter, "__aiter__"):
            raise TypeError("stream_recognize must return an async iterator")
        async for res in stream_iter:
            time_end = res.time_end if res.time_end is not None else audio_clock.now_s()
            time_start = res.time_start if res.time_start is not None else last_end
            if time_end < time_start:
                time_end = time_start
            last_end = time_end

            transcript_payload: Dict[str, Any] = {
                "meeting_id": session_id,
                "chunk": res.text,
                "speaker": res.speaker or "SPEAKER_01",
                "time_start": float(time_start),
                "time_end": float(time_end),
                "is_final": bool(res.is_final),
                "confidence": float(res.confidence),
                "lang": res.lang or "vi",
                "question": False,
            }
            try:
                await ingestTranscript(session_id, transcript_payload, source="smartvoice_stt")
            except Exception:
                pass
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("smartvoice stream failed (session_id=%s)", session_id)
        try:
            await _safe_send_json(
                websocket,
                send_lock,
                {
                    "event": "error",
                    "session_id": session_id,
                    "message": f"smartvoice_error: {exc}",
                },
            )
        except Exception:
            pass


@router.websocket("/audio/{session_id}")
async def audio_ingest(websocket: WebSocket, session_id: str):
    token = websocket.query_params.get("token")
    if not token or not verify_audio_ingest_token(token, expected_session_id=session_id):
        await websocket.close(code=1008)
        return

    session = session_store.get(session_id)
    if not session:
        await websocket.accept()
        await websocket.send_json(
            {
                "event": "error",
                "session_id": session_id,
                "message": "Session not found. Create it via POST /api/v1/sessions first.",
            }
        )
        await websocket.close(code=1008)
        return

    await websocket.accept()
    await websocket.send_json({"event": "connected", "channel": "audio", "session_id": session_id})
    send_lock = asyncio.Lock()
    _ensure_stream_worker(session_id)

    try:
        raw = await websocket.receive_text()
        start_msg = AudioStartMessage.model_validate(json.loads(raw))
    except Exception as exc:
        await _safe_send_json(
            websocket,
            send_lock,
            {"event": "error", "session_id": session_id, "message": f"invalid_start: {exc}"},
        )
        await websocket.close(code=1003)
        return

    expected = session.config.expected_audio
    if (
        start_msg.audio.codec != expected.codec
        or start_msg.audio.sample_rate_hz != expected.sample_rate_hz
        or start_msg.audio.channels != expected.channels
    ):
        await _safe_send_json(
            websocket,
            send_lock,
            {
                "event": "error",
                "session_id": session_id,
                "message": "audio_format_mismatch",
                "expected_audio": {
                    "codec": expected.codec,
                    "sample_rate_hz": expected.sample_rate_hz,
                    "channels": expected.channels,
                },
            },
        )
        await websocket.close(code=1003)
        return

    stt_param = (websocket.query_params.get("stt") or "").strip().lower()
    if stt_param in {"0", "false", "off", "no"}:
        stt_enabled = False
    elif stt_param in {"1", "true", "on", "yes"}:
        stt_enabled = True
    else:
        stt_enabled = is_smartvoice_configured()

    await _safe_send_json(
        websocket,
        send_lock,
        {
            "event": "audio_start_ack",
            "session_id": session_id,
            "accepted_audio": {
                "codec": expected.codec,
                "sample_rate_hz": expected.sample_rate_hz,
                "channels": expected.channels,
            },
            "stt_enabled": stt_enabled,
        },
    )

    audio_queue: asyncio.Queue[Optional[bytes]] | None = None
    audio_clock = _AudioClock(sample_rate_hz=expected.sample_rate_hz, channels=expected.channels)
    stt_task: asyncio.Task | None = None
    if stt_enabled:
        audio_queue = asyncio.Queue(maxsize=50)
        stt_cfg = SmartVoiceStreamingConfig(
            language_code=start_msg.language_code or session.config.language_code,
            sample_rate_hz=expected.sample_rate_hz,
            interim_results=session.config.interim_results,
            enable_word_time_offsets=session.config.enable_word_time_offsets,
        )
        stt_task = asyncio.create_task(
            _smartvoice_to_bus(session_id, audio_queue, stt_cfg, audio_clock, websocket, send_lock)
        )
    else:
        try:
            await _safe_send_json(
                websocket,
                send_lock,
                {"event": "stt_disabled", "session_id": session_id, "reason": "smartvoice_not_configured_or_disabled"},
            )
        except Exception:
            pass

    ingest_ok_sent = False
    received_bytes = 0
    received_frames = 0

    try:
        while True:
            if stt_task is not None and stt_task.done():
                break
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if message.get("bytes") is not None:
                chunk = message["bytes"]
                if chunk:
                    received_bytes += len(chunk)
                    received_frames += 1
                    if not ingest_ok_sent:
                        ingest_ok_sent = True
                        await _safe_send_json(
                            websocket,
                            send_lock,
                            {
                                "event": "audio_ingest_ok",
                                "session_id": session_id,
                                "received_bytes": received_bytes,
                                "received_frames": received_frames,
                            },
                        )

                    if audio_queue is not None:
                        if audio_queue.full():
                            suggested = min(
                                max(start_msg.frame_ms * 2, session.config.recommended_frame_ms),
                                session.config.max_frame_ms,
                            )
                            await _safe_send_json(
                                websocket,
                                send_lock,
                                {"event": "throttle", "reason": "stt_backpressure", "suggested_frame_ms": suggested},
                            )
                        await audio_queue.put(chunk)
                    audio_clock.advance(len(chunk))
                    session_store.touch(session_id)
                continue

            if message.get("text") is not None:
                try:
                    obj = json.loads(message["text"])
                    if obj.get("type") == "stop":
                        break
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        if audio_queue is not None:
            try:
                audio_queue.put_nowait(None)
            except Exception:
                try:
                    await audio_queue.put(None)
                except Exception:
                    pass
        if stt_task is not None:
            try:
                await asyncio.wait_for(stt_task, timeout=5)
            except Exception:
                stt_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/in-meeting/{session_id}")
async def in_meeting_ingest(websocket: WebSocket, session_id: str):
    await websocket.accept()
    await websocket.send_json({"event": "connected", "channel": "ingest", "session_id": session_id})
    session_store.ensure(session_id)
    _ensure_stream_worker(session_id)
    try:
        while True:
            try:
                payload = await websocket.receive_json()
            except WebSocketDisconnect:
                break
            except Exception as exc:
                await websocket.send_json({"event": "error", "session_id": session_id, "message": str(exc)})
                continue

            meeting_id = payload.get("meeting_id") or session_id
            chunk_text = payload.get("chunk") or payload.get("text") or ""
            transcript_payload: Dict[str, Any] = {
                "meeting_id": meeting_id,
                "chunk": chunk_text,
                "speaker": payload.get("speaker", "SPEAKER_01"),
                "time_start": payload.get("time_start", 0.0),
                "time_end": payload.get("time_end", 0.0),
                "is_final": payload.get("is_final", True),
                "confidence": payload.get("confidence", 1.0),
                "lang": payload.get("lang", "vi"),
                "question": payload.get("question"),
            }
            try:
                seq = await ingestTranscript(session_id, transcript_payload, source="transcript_test_ws")
                await websocket.send_json({"event": "ingest_ack", "session_id": session_id, "seq": seq})
            except Exception as exc:
                await websocket.send_json({"event": "error", "session_id": session_id, "message": str(exc)})
            _ensure_stream_worker(session_id)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/frontend/{session_id}")
async def in_meeting_frontend(websocket: WebSocket, session_id: str):
    await websocket.accept()
    queue = session_bus.subscribe(session_id)
    await websocket.send_json({"event": "connected", "channel": "frontend", "session_id": session_id})
    try:
        while True:
            try:
                event = await queue.get()
            except asyncio.CancelledError:
                break
            if event.get("event") == "transcript_event":
                # Keep frontend contract minimal; strip internal-only fields.
                payload = dict(event.get("payload") or {})
                payload.pop("transcript_window", None)
                payload.pop("source", None)
                payload.pop("question", None)
                cleaned = dict(event)
                cleaned["payload"] = payload
                await websocket.send_json(cleaned)
            else:
                await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        session_bus.unsubscribe(session_id, queue)
        try:
            await websocket.close()
        except Exception:
            pass
