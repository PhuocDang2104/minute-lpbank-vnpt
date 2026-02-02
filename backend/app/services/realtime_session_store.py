from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional


@dataclass(frozen=True)
class ExpectedAudio:
    codec: str = "PCM_S16LE"
    sample_rate_hz: int = 16000
    channels: int = 1


@dataclass
class RealtimeSessionConfig:
    language_code: str = "vi-VN"
    expected_audio: ExpectedAudio = field(default_factory=ExpectedAudio)
    interim_results: bool = True
    enable_word_time_offsets: bool = True
    recommended_frame_ms: int = 250
    max_frame_ms: int = 1000


@dataclass
class RealtimeSession:
    session_id: str
    config: RealtimeSessionConfig
    created_at_s: float = field(default_factory=time.time)
    last_activity_s: float = field(default_factory=time.time)

    transcript_buffer: str = ""
    state_version: int = 0
    stream_state: "InMeetingStreamState" = field(default_factory=lambda: InMeetingStreamState())


@dataclass
class FinalTranscriptChunk:
    seq: int
    time_start: float
    time_end: float
    speaker: str
    lang: str
    confidence: float
    text: str


@dataclass
class InMeetingStreamState:
    final_stream: List[FinalTranscriptChunk] = field(default_factory=list)
    final_by_seq: Dict[int, FinalTranscriptChunk] = field(default_factory=dict)
    speaker_segments: List[Dict[str, Any]] = field(default_factory=list)
    rolling_window: Deque[FinalTranscriptChunk] = field(default_factory=deque)
    last_final_seq: int = 0
    last_transcript_seq: int = 0
    last_transcript_chunk: Optional[FinalTranscriptChunk] = None
    last_transcript_is_final: bool = True
    last_partial_seq: int = 0
    last_partial_chunk: Optional[FinalTranscriptChunk] = None
    recap_cursor_seq: int = 0
    last_recap_tick_at: float = 0.0
    last_recap_tick_anchor: float = 0.0
    max_seen_time_end: float = 0.0
    current_topic_id: Optional[str] = None
    semantic_intent_label: Optional[str] = None
    semantic_intent_slots: Dict[str, Any] = field(default_factory=dict)
    last_live_recap: Optional[str] = None
    last_recap: Optional[str] = None
    last_topic_payload: Dict[str, Any] = field(default_factory=dict)
    last_intent_payload: Dict[str, Any] = field(default_factory=dict)
    topic_segments: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)


class RealtimeSessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, RealtimeSession] = {}
        self._lock = threading.Lock()

    def create(self, config: RealtimeSessionConfig) -> RealtimeSession:
        session_id = str(uuid.uuid4())
        session = RealtimeSession(session_id=session_id, config=config)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def create_with_id(self, session_id: str, config: RealtimeSessionConfig) -> RealtimeSession:
        session = RealtimeSession(session_id=session_id, config=config)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Optional[RealtimeSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def ensure(self, session_id: str, config: Optional[RealtimeSessionConfig] = None) -> RealtimeSession:
        with self._lock:
            existing = self._sessions.get(session_id)
            if existing:
                existing.last_activity_s = time.time()
                return existing
            session = RealtimeSession(
                session_id=session_id,
                config=config or RealtimeSessionConfig(),
            )
            self._sessions[session_id] = session
            return session

    def touch(self, session_id: str) -> None:
        with self._lock:
            sess = self._sessions.get(session_id)
            if sess:
                sess.last_activity_s = time.time()

    def append_transcript(self, session_id: str, text: str, max_chars: int = 4000) -> str:
        if not text:
            with self._lock:
                sess = self._sessions.get(session_id)
                return sess.transcript_buffer if sess else ""

        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                sess = RealtimeSession(session_id=session_id, config=RealtimeSessionConfig())
                self._sessions[session_id] = sess
            combined = f"{sess.transcript_buffer}\n{text}".strip() if sess.transcript_buffer else text.strip()
            if len(combined) > max_chars:
                combined = combined[-max_chars:]
            sess.transcript_buffer = combined
            sess.last_activity_s = time.time()
            return combined

    def next_state_version(self, session_id: str) -> int:
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                sess = RealtimeSession(session_id=session_id, config=RealtimeSessionConfig())
                self._sessions[session_id] = sess
            sess.state_version = (sess.state_version or 0) + 1
            sess.last_activity_s = time.time()
            return sess.state_version


session_store = RealtimeSessionStore()
