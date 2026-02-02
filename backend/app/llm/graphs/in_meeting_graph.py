from typing import List
from app.llm.graphs.state import (
    MeetingState,
    StateGraph,
    END,
    ActionItem,
    Decision,
    Risk,
)
from app.llm.chains.in_meeting_chain import summarize_transcript, extract_adr, answer_question, segment_topic
from app.llm.tools.smartbot_intent_tool import predict_intent
from app.llm.tools.rag_search_tool import rag_retrieve


COMMAND_INTENTS = {
    "ACTION_COMMAND",
    "SCHEDULE_COMMAND",
    "DECISION_STATEMENT",
    "RISK_STATEMENT",
}


def _trim_window(text: str, max_chars: int = 1200) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _merge_list(existing: list, new_items: list, key: str = "task") -> list:
    seen = set()
    merged = []
    for item in (existing or []) + (new_items or []):
        value = item.get(key)
        if value in seen:
            continue
        seen.add(value)
        merged.append(item)
    return merged


def build_in_meeting_subgraph():
    graph = StateGraph(MeetingState)

    def init_node(state: MeetingState) -> MeetingState:
        state.setdefault("stage", "in")
        state.setdefault("intent", "tick")
        state.setdefault("sensitivity", "medium")
        state.setdefault("sla", "realtime")
        state.setdefault("transcript_window", "")
        state.setdefault("full_transcript", "")
        state.setdefault("semantic_intent_label", "NO_INTENT")
        state.setdefault("semantic_intent_slots", {})
        # Normalize collections to lists
        if not isinstance(state.get("topic_segments"), list):
            state["topic_segments"] = []
        state.setdefault("current_topic_id", None)
        for key in ["actions", "decisions", "risks", "new_actions", "new_decisions", "new_risks", "rag_docs", "tool_suggestions", "citations"]:
            if not isinstance(state.get(key), list):
                state[key] = []
        state.setdefault("debug_info", {})
        return state

    def semantic_router_node(state: MeetingState) -> MeetingState:
        seg = state.get("vnpt_segment") or {}
        text = seg.get("text") or state.get("transcript_window") or ""
        intent_label, intent_slots = predict_intent(text=text, lang=seg.get("lang", "vi"))
        state["semantic_intent_label"] = intent_label or "NO_INTENT"
        state["semantic_intent_slots"] = intent_slots or {}
        state["debug_info"]["semantic_intent"] = {
            "label": state["semantic_intent_label"],
            "slots": state["semantic_intent_slots"],
            "source": "smartbot_intent_tool",
        }
        return state

    def update_transcript_window_node(state: MeetingState) -> MeetingState:
        seg = state.get("vnpt_segment") or {}
        text = seg.get("text")
        is_final = seg.get("is_final", True)
        if text:
            if is_final:
                state["full_transcript"] = f"{state.get('full_transcript', '')}\n{text}".strip()
            window = f"{state.get('transcript_window', '')}\n{text}".strip()
            state["transcript_window"] = _trim_window(window)
        state["debug_info"]["transcript_window_len"] = len(state.get("transcript_window", ""))
        return state

    def topic_segmenter_node(state: MeetingState) -> MeetingState:
        # Normalize topic_segments to list
        if not isinstance(state.get("topic_segments"), list):
            state["topic_segments"] = []
        payload = segment_topic(
            transcript_window=state.get("transcript_window") or "",
            current_topic_id=state.get("current_topic_id"),
        )
        if payload.get("new_topic") or not state.get("topic_segments"):
            state.setdefault("topic_segments", [])
            state["topic_segments"].append({
                "topic_id": payload.get("topic_id") or "T0",
                "title": payload.get("title") or "General",
                "start_t": payload.get("start_t", state.get("vnpt_segment", {}).get("time_start", 0.0)),
                "end_t": payload.get("end_t", state.get("vnpt_segment", {}).get("time_end", 0.0)),
            })
        state["current_topic_id"] = payload.get("topic_id") or state.get("current_topic_id") or "T0"
        return state

    def live_recap_node(state: MeetingState) -> MeetingState:
        recap = summarize_transcript(
            transcript_window=state.get("transcript_window") or "",
            topic=state.get("current_topic_id"),
            intent=state.get("semantic_intent_label"),
        )
        state["debug_info"]["recap"] = recap
        return state

    def adr_extractor_node(state: MeetingState) -> MeetingState:
        extraction = extract_adr(
            transcript_window=state.get("transcript_window") or "",
            topic_id=state.get("current_topic_id"),
        )
        new_actions = extraction.get("actions", [])
        new_decisions = extraction.get("decisions", [])
        new_risks = extraction.get("risks", [])

        state["new_actions"] = new_actions
        state["new_decisions"] = new_decisions
        state["new_risks"] = new_risks

        state["actions"] = _merge_list(state.get("actions", []), new_actions, key="task")
        state["decisions"] = _merge_list(state.get("decisions", []), new_decisions, key="title")
        state["risks"] = _merge_list(state.get("risks", []), new_risks, key="desc")
        return state

    def qa_prepare_node(state: MeetingState) -> MeetingState:
        question = state.get("last_user_question")
        if not question:
            question = (state.get("semantic_intent_slots") or {}).get("question")
        state["last_user_question"] = question
        state["debug_info"]["qa_question"] = question
        return state

    def qa_rag_node(state: MeetingState) -> MeetingState:
        question = state.get("last_user_question")
        if not question:
            return state
        rag_docs = rag_retrieve(
            question=question,
            meeting_id=state.get("meeting_id"),
            topic_id=state.get("current_topic_id"),
            project_id=state.get("project_id"),
        )
        state["rag_docs"] = rag_docs or []
        return state

    def qa_answer_node(state: MeetingState) -> MeetingState:
        question = state.get("last_user_question")
        if not question:
            return state
        answer_payload = answer_question(
            question=question,
            rag_docs=state.get("rag_docs") or [],
            transcript_window=state.get("transcript_window") or "",
        )
        state["last_qa_answer"] = answer_payload.get("answer")
        state["citations"] = answer_payload.get("citations", [])
        state["debug_info"]["qa_answer"] = state["last_qa_answer"]
        return state

    def command_to_adr_node(state: MeetingState) -> MeetingState:
        slots = state.get("semantic_intent_slots") or {}
        intent = state.get("semantic_intent_label", "")
        new_actions: List[ActionItem] = []
        new_decisions: List[Decision] = []
        new_risks: List[Risk] = []

        if intent == "ACTION_COMMAND":
            new_actions.append(
                ActionItem(
                    task=slots.get("task") or "Follow-up action",
                    owner=slots.get("owner"),
                    due_date=slots.get("due_date"),
                    priority=slots.get("priority"),
                    topic_id=state.get("current_topic_id"),
                )
            )
        if intent == "DECISION_STATEMENT":
            new_decisions.append(
                Decision(
                    title=slots.get("title") or "Decision recorded",
                    rationale=slots.get("rationale"),
                    impact=slots.get("impact"),
                )
            )
        if intent in {"RISK_STATEMENT", "SCHEDULE_COMMAND"}:
            new_risks.append(
                Risk(
                    desc=slots.get("risk") or slots.get("desc") or "Risk noted",
                    severity=slots.get("severity"),
                    mitigation=slots.get("mitigation"),
                    owner=slots.get("owner"),
                )
            )

        state["new_actions"] = new_actions
        state["new_decisions"] = new_decisions
        state["new_risks"] = new_risks
        state["actions"] = _merge_list(state.get("actions", []), new_actions, key="task")
        state["decisions"] = _merge_list(state.get("decisions", []), new_decisions, key="title")
        state["risks"] = _merge_list(state.get("risks", []), new_risks, key="desc")
        return state

    def tool_suggestion_node(state: MeetingState) -> MeetingState:
        suggestions = []
        for action in state.get("new_actions", []):
            suggestions.append({
                "suggestion_id": f"task-{len(suggestions)+1}",
                "type": "task",
                "action_hash": action.get("task"),
                "payload": {"task": action.get("task"), "owner": action.get("owner"), "due": action.get("due_date")},
            })
        for risk in state.get("new_risks", []):
            suggestions.append({
                "suggestion_id": f"schedule-{len(suggestions)+1}",
                "type": "schedule",
                "action_hash": risk.get("desc"),
                "payload": {"title": risk.get("desc"), "owner": risk.get("owner")},
            })
        state["tool_suggestions"] = suggestions
        state["debug_info"]["tool_suggestions"] = suggestions
        return state

    graph.add_node("init", init_node)
    graph.add_node("semantic_router", semantic_router_node)
    graph.add_node("update_transcript_window_normal", update_transcript_window_node)
    graph.add_node("update_transcript_window_qa", update_transcript_window_node)
    graph.add_node("update_transcript_window_command", update_transcript_window_node)
    graph.add_node("topic_segmenter", topic_segmenter_node)
    graph.add_node("live_recap", live_recap_node)
    graph.add_node("adr_extractor", adr_extractor_node)
    graph.add_node("qa_prepare", qa_prepare_node)
    graph.add_node("qa_rag", qa_rag_node)
    graph.add_node("qa_answer", qa_answer_node)
    graph.add_node("command_to_adr", command_to_adr_node)
    graph.add_node("tool_suggestion", tool_suggestion_node)

    graph.set_entry_point("init")
    graph.add_edge("init", "semantic_router")

    def flow_router(state: MeetingState):
        if state.get("intent") == "qa":
            return "qa"
        if state.get("semantic_intent_label") in COMMAND_INTENTS:
            return "command"
        if state.get("semantic_intent_label") == "ASK_AI":
            return "qa"
        return "normal"

    graph.add_conditional_edges(
        "semantic_router",
        flow_router,
        {
            "normal": "update_transcript_window_normal",
            "qa": "update_transcript_window_qa",
            "command": "update_transcript_window_command",
        },
    )

    # Normal flow
    graph.add_edge("update_transcript_window_normal", "topic_segmenter")
    graph.add_edge("topic_segmenter", "live_recap")
    graph.add_edge("live_recap", "adr_extractor")
    graph.add_edge("adr_extractor", END)

    # Q&A flow
    graph.add_edge("update_transcript_window_qa", "qa_prepare")
    graph.add_edge("qa_prepare", "qa_rag")
    graph.add_edge("qa_rag", "qa_answer")
    graph.add_edge("qa_answer", "live_recap")

    # Command flow
    graph.add_edge("update_transcript_window_command", "command_to_adr")
    graph.add_edge("command_to_adr", "tool_suggestion")
    graph.add_edge("tool_suggestion", "live_recap")

    return graph.compile()


# Backward-compatible alias
build_in_meeting_graph = build_in_meeting_subgraph
