from app.llm.graphs.state import MeetingState, StateGraph, END


def build_post_meeting_subgraph():
    graph = StateGraph(MeetingState)

    def consolidate_node(state: MeetingState) -> MeetingState:
        state.setdefault("stage", "post")
        state.setdefault("full_transcript", state.get("full_transcript", ""))
        state.setdefault("actions", [])
        state.setdefault("decisions", [])
        state.setdefault("risks", [])
        state.setdefault("debug_info", {})
        state["debug_info"]["post_consolidated"] = True
        return state

    def summary_node(state: MeetingState) -> MeetingState:
        summary = "Post-meeting summary stub. Populate via MoM generator chain."
        state["debug_info"]["post_summary"] = summary
        return state

    graph.add_node("consolidate", consolidate_node)
    graph.add_node("summary", summary_node)
    graph.set_entry_point("consolidate")
    graph.add_edge("consolidate", "summary")
    graph.add_edge("summary", END)
    return graph.compile()


# Backward-compatible alias
build_post_meeting_graph = build_post_meeting_subgraph
