import time
from typing import Dict, Any
from app.llm.agents.base_agent import BaseAgent
from app.llm.graphs.router import build_router_graph


class InMeetingScheduler:
    """Tick scheduler to throttle LLM calls."""

    def __init__(self, interval_sec: int = 15, token_threshold: int = 120) -> None:
        self.interval_sec = interval_sec
        self.token_threshold = token_threshold
        self.last_llm_ts = 0.0
        self.buffer_tokens = 0

    def update_tokens(self, text: str) -> None:
        self.buffer_tokens += len((text or "").split())

    def should_run(self, force: bool = False) -> bool:
        now = time.time()
        if force:
            self.last_llm_ts = now
            self.buffer_tokens = 0
            return True
        if (now - self.last_llm_ts) >= self.interval_sec or self.buffer_tokens >= self.token_threshold:
            self.last_llm_ts = now
            self.buffer_tokens = 0
            return True
        return False


class InMeetingAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(build_router_graph(default_stage="in"), stage="in")
        self.scheduler = InMeetingScheduler()

    def run_with_scheduler(self, state: Dict[str, Any], force: bool = False) -> Dict[str, Any] | None:
        text = ""
        seg = state.get("vnpt_segment") or {}
        if seg:
            text = seg.get("text", "")
        else:
            text = state.get("transcript_window", "")

        self.scheduler.update_tokens(text or "")
        should = self.scheduler.should_run(force=force)
        state.setdefault("debug_info", {})
        state["debug_info"]["llm_tick_scheduled"] = should
        state["debug_info"]["buffer_tokens"] = self.scheduler.buffer_tokens
        if not should:
            return None
        return self.run(state)
