from typing import Any


class OpenAIClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def chat(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        # Stub: echo back last user message
        last = messages[-1]['content'] if messages else ''
        return {"content": f"echo: {last}", "model": "stub-openai"}