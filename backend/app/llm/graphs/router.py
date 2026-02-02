from typing import Literal
from app.llm.graphs.state import MeetingState, StateGraph, END
from app.llm.graphs.in_meeting_graph import build_in_meeting_subgraph
from app.llm.graphs.pre_meeting_graph import build_pre_meeting_subgraph
from app.llm.graphs.post_meeting_graph import build_post_meeting_subgraph

GraphStage = Literal["pre", "in", "post"]


def router_node(default_stage: GraphStage):
    def _router(state: MeetingState) -> MeetingState:
        stage = state.get("stage", default_stage)
        state.setdefault("debug_info", {})
        state["debug_info"]["router_stage"] = stage
        return state

    return _router


def build_router_graph(default_stage: GraphStage = "in"):
    workflow = StateGraph(MeetingState)

    workflow.add_node("router", router_node(default_stage))

    pre_graph = build_pre_meeting_subgraph()
    in_graph = build_in_meeting_subgraph()
    post_graph = build_post_meeting_subgraph()

    workflow.add_node("pre_meeting", pre_graph)
    workflow.add_node("in_meeting", in_graph)
    workflow.add_node("post_meeting", post_graph)

    workflow.set_entry_point("router")

    def route_decider(state: MeetingState):
        stage = state.get("stage")
        if stage == "pre":
            return "pre_meeting"
        if stage == "in":
            return "in_meeting"
        return "post_meeting"

    workflow.add_conditional_edges(
        "router",
        route_decider,
        {
            "pre_meeting": "pre_meeting",
            "in_meeting": "in_meeting",
            "post_meeting": "post_meeting",
        },
    )

    workflow.add_edge("pre_meeting", END)
    workflow.add_edge("in_meeting", END)
    workflow.add_edge("post_meeting", END)

    return workflow.compile()


# Backward-compatible factory for legacy imports
def build_router(stage: GraphStage):
    return build_router_graph(stage)
