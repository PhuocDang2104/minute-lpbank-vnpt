from typing import Any
from app.vectorstore.retrieval import simple_retrieval
from app.llm.clients.openai_client import OpenAIClient


def run_rag(query: str, meeting_id: str | None = None) -> dict[str, Any]:
    docs = simple_retrieval(query, meeting_id)
    llm = OpenAIClient()
    answer = llm.chat([{"role": "user", "content": query}])['content']
    return {"answer": answer, "citations": docs}