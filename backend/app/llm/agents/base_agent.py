from typing import Any, Optional


class BaseAgent:
    def __init__(self, graph: Any, stage: Optional[str] = None) -> None:
        self.graph = graph
        self.stage = stage

    def run(self, state: dict) -> dict:
        payload = dict(state or {})
        if self.stage and "stage" not in payload:
            payload["stage"] = self.stage

        if hasattr(self.graph, "invoke"):
            return self.graph.invoke(payload)
        return payload

    async def arun(self, state: dict) -> dict:
        payload = dict(state or {})
        if self.stage and "stage" not in payload:
            payload["stage"] = self.stage

        if hasattr(self.graph, "ainvoke"):
            return await self.graph.ainvoke(payload)
        if hasattr(self.graph, "invoke"):
            return self.graph.invoke(payload)
        return payload
