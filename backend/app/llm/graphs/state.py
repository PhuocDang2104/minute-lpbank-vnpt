from typing import List, Optional, Literal, TypedDict, Dict, Any


try:
    from langgraph.graph import StateGraph, END  # type: ignore
except ImportError:
    # Lightweight stub so the codebase still works without langgraph installed.
    class StateGraph:  # type: ignore
        def __init__(self, *_args, **_kwargs):
            self.nodes = {}
            self.edges = []
            self.conditional_edges = []
            self.entry_point = None

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def set_entry_point(self, name):
            self.entry_point = name

        def add_edge(self, start, end):
            self.edges.append((start, end))

        def add_conditional_edges(self, start, decider, mapping):
            self.conditional_edges.append((start, decider, mapping))

        def _invoke_node(self, name, state):
            node = self.nodes.get(name)
            if callable(node):
                return node(state)
            if hasattr(node, "invoke"):
                return node.invoke(state)
            return state

        def invoke(self, state):
            current = self.entry_point or (next(iter(self.nodes)) if self.nodes else None)
            if current:
                state = self._invoke_node(current, state)

            while True:
                advanced = False
                for src, dest in list(self.edges):
                    if src == current:
                        if dest == END:
                            return state
                        state = self._invoke_node(dest, state)
                        current = dest
                        advanced = True
                        break

                if advanced:
                    continue

                for src, decider, mapping in list(self.conditional_edges):
                    if src == current:
                        key = decider(state)
                        dest = mapping.get(key)
                        if dest:
                            state = self._invoke_node(dest, state)
                            current = dest
                            advanced = True
                            break

                if not advanced:
                    return state

        async def ainvoke(self, state):
            return self.invoke(state)

        def __call__(self, state):
            return self.invoke(state)

        def compile(self):
            return self

    END = "END"


class VNPTSegment(TypedDict, total=False):
    text: str
    time_start: float
    time_end: float
    speaker: str
    is_final: bool
    confidence: float
    lang: Optional[str]


class TopicSegment(TypedDict, total=False):
    topic_id: str
    title: str
    start_t: float
    end_t: float


class Decision(TypedDict, total=False):
    title: str
    rationale: Optional[str]
    impact: Optional[str]
    source_timecode: Optional[float]


class Risk(TypedDict, total=False):
    desc: str
    severity: Optional[str]
    mitigation: Optional[str]
    owner: Optional[str]
    source_timecode: Optional[float]


class ActionItem(TypedDict, total=False):
    task: str
    owner: Optional[str]
    due_date: Optional[str]
    priority: Optional[str]
    source_timecode: Optional[float]
    topic_id: Optional[str]
    external_id: Optional[str]


class ToolSuggestion(TypedDict, total=False):
    suggestion_id: str
    type: Literal["task", "schedule", "doc", "other"]
    action_hash: Optional[str]
    payload: Dict[str, Any]


class MeetingState(TypedDict, total=False):
    meeting_id: str
    stage: Literal["pre", "in", "post"]
    intent: Literal["tick", "qa", "system"]
    project_id: Optional[str]
    sensitivity: Literal["low", "medium", "high"]
    sla: Literal["realtime", "near_realtime", "batch"]

    vnpt_segment: VNPTSegment
    transcript_window: str  # rolling window (10-30s or N sentences)
    full_transcript: str
    semantic_intent_label: Optional[str]
    semantic_intent_slots: Dict[str, Any]
    last_user_question: Optional[str]
    last_qa_answer: Optional[str]
    citations: list

    topic_segments: List[TopicSegment]
    current_topic_id: Optional[str]

    rag_docs: list
    actions: List[ActionItem]
    decisions: List[Decision]
    risks: List[Risk]
    new_actions: List[ActionItem]
    new_decisions: List[Decision]
    new_risks: List[Risk]

    tool_suggestions: List[ToolSuggestion]

    debug_info: Dict[str, Any]
