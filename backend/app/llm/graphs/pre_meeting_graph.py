from app.llm.graphs.state import MeetingState, StateGraph, END


def build_pre_meeting_subgraph():
    graph = StateGraph(MeetingState)

    def prepare_context(state: MeetingState) -> MeetingState:
        state.setdefault("stage", "pre")
        state.setdefault("rag_docs", [])
        state.setdefault("citations", [])
        debug = state.setdefault("debug_info", {})
        debug["pre_context_ready"] = True
        return state

    def agenda_stub(state: MeetingState) -> MeetingState:
        state.setdefault("rag_docs", [])
        agenda = [
            {"order": 1, "title": "Khai mạc & điểm danh", "duration_minutes": 5, "presenter": "Chair"},
            {"order": 2, "title": "Báo cáo tiến độ", "duration_minutes": 15, "presenter": "PM"},
            {"order": 3, "title": "Rủi ro & blockers", "duration_minutes": 20, "presenter": "PMO"},
            {"order": 4, "title": "Quyết định & Action Items", "duration_minutes": 10, "presenter": "Leads"},
            {"order": 5, "title": "Kết luận", "duration_minutes": 5, "presenter": "Chair"},
        ]
        state["debug_info"]["agenda_suggestion"] = agenda
        return state

    graph.add_node("prepare_context", prepare_context)
    graph.add_node("agenda", agenda_stub)
    graph.set_entry_point("prepare_context")
    graph.add_edge("prepare_context", "agenda")
    graph.add_edge("agenda", END)
    return graph.compile()


# Backward-compatible alias
build_pre_meeting_graph = build_pre_meeting_subgraph
