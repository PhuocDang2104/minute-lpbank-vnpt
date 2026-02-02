from typing import Literal, Dict, Any
from fastapi import APIRouter, Body
from app.llm.graphs.router import build_router_graph
from app.llm.graphs.state import MeetingState

router = APIRouter()
router_graph = build_router_graph()


def _run_graph(state: MeetingState) -> Dict[str, Any]:
    if hasattr(router_graph, "invoke"):
        return router_graph.invoke(state)  # type: ignore[return-value]
    return state  # type: ignore[return-value]


@router.post('/{stage}', response_model=dict)
async def run_agent(stage: Literal["pre", "in", "post"], payload: Dict[str, Any] = Body(default_factory=dict)):
    """
    Run LangGraph router with a given stage.
    - Provide any partial MeetingState in the payload (transcript_window, question, etc.).
    - The router will dispatch to the corresponding subgraph stub.
    """
    state: MeetingState = {"stage": stage}
    state.update(payload or {})

    if hasattr(router_graph, "ainvoke"):
        return await router_graph.ainvoke(state)  # type: ignore[return-value]
    return _run_graph(state)
