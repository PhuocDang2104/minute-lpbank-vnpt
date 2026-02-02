import time

from app.api.v1.websocket import in_meeting_ws
from app.llm.chains import in_meeting_chain
from app.services.realtime_session_store import FinalTranscriptChunk, InMeetingStreamState


def _chunk(seq: int, start: float, end: float, text: str) -> FinalTranscriptChunk:
    return FinalTranscriptChunk(
        seq=seq,
        time_start=start,
        time_end=end,
        speaker="SPEAKER_01",
        lang="vi",
        confidence=0.9,
        text=text,
    )


def test_select_window_includes_partial_latest() -> None:
    state = InMeetingStreamState()
    c1 = _chunk(1, 0.0, 10.0, "hello")
    c2 = _chunk(2, 10.0, 40.0, "world")
    state.rolling_window.extend([c1, c2])
    state.max_seen_time_end = c2.time_end
    state.last_final_seq = c2.seq
    state.last_partial_seq = 3
    state.last_partial_chunk = _chunk(3, 40.0, 55.0, "partial")

    chunks = in_meeting_ws._select_window_chunks(state, 60.0, include_partial=True)

    assert chunks
    assert chunks[-1].seq == 3
    assert chunks[-1].text == "partial"


def test_should_recap_tick_requires_new_transcript_and_interval() -> None:
    state = InMeetingStreamState()
    now = 200.0
    state.last_transcript_seq = 5
    state.recap_cursor_seq = 5
    state.last_recap_tick_at = now - (in_meeting_ws.RECAP_TICK_SEC + 1)
    assert in_meeting_ws._should_recap_tick(state, now) is False

    state.recap_cursor_seq = 4
    state.max_seen_time_end = 20.0
    assert in_meeting_ws._should_recap_tick(state, now) is False

    state.max_seen_time_end = 40.0
    assert in_meeting_ws._should_recap_tick(state, now) is True

    state.last_recap_tick_anchor = 20.0
    assert in_meeting_ws._should_recap_tick(state, now) is False


def test_summarize_and_classify_fallback_on_bad_json(monkeypatch) -> None:
    def _fake_call(_: str) -> str:
        return "not-json"

    monkeypatch.setattr(in_meeting_chain, "_call_gemini", _fake_call)
    meta = {"current_topic_id": "T9"}
    result = in_meeting_chain.summarize_and_classify("test transcript", meta=meta)

    assert result["intent"]["label"] == "NO_INTENT"
    assert result["topic"]["topic_id"] == "T9"
    assert result["recap"].startswith("Status:")
    assert meta.get("parse_ok") is False


def test_run_recap_tick_updates_cursor_and_payload(monkeypatch) -> None:
    def _fake_summary(_: str, meta: dict) -> dict:
        return {
            "recap": "Status: ok",
            "topic": {
                "new_topic": True,
                "topic_id": "T1",
                "title": "Alpha",
                "start_t": 0.0,
                "end_t": 20.0,
            },
            "intent": {"label": "DECISION_STATEMENT", "slots": {"title": "Approved"}},
        }

    monkeypatch.setattr(in_meeting_ws, "summarize_and_classify", _fake_summary)

    state = InMeetingStreamState()
    c1 = _chunk(1, 0.0, 20.0, "hello")
    c2 = _chunk(2, 20.0, 40.0, "world")
    state.rolling_window.extend([c1, c2])
    state.max_seen_time_end = c2.time_end
    state.last_transcript_seq = 2
    state.last_final_seq = 2
    now = time.time()

    payload = in_meeting_ws._run_recap_tick("sess-1", state, now)

    assert payload is not None
    assert payload["recap"] == "Status: ok"
    assert payload["topic"]["topic_id"] == "T1"
    assert payload["intent_payload"]["label"] == "DECISION_STATEMENT"
    assert "transcript_window" in payload
    assert state.recap_cursor_seq == 2
    assert state.semantic_intent_label == "DECISION_STATEMENT"
    assert state.current_topic_id == "T1"

    assert in_meeting_ws._should_recap_tick(state, now) is False


def test_run_recap_tick_skips_short_window(monkeypatch) -> None:
    def _fake_summary(_: str, meta: dict) -> dict:
        return {
            "recap": "Status: ok",
            "topic": {"new_topic": False, "topic_id": "T0", "title": "General", "start_t": 0.0, "end_t": 10.0},
            "intent": {"label": "NO_INTENT", "slots": {}},
        }

    monkeypatch.setattr(in_meeting_ws, "summarize_and_classify", _fake_summary)

    state = InMeetingStreamState()
    c1 = _chunk(1, 0.0, 10.0, "short")
    state.rolling_window.append(c1)
    state.max_seen_time_end = c1.time_end
    state.last_transcript_seq = 1
    state.last_final_seq = 1
    now = time.time()

    payload = in_meeting_ws._run_recap_tick("sess-2", state, now)

    assert payload is None
    assert state.recap_cursor_seq == 1
    assert state.last_recap_tick_anchor == state.max_seen_time_end
