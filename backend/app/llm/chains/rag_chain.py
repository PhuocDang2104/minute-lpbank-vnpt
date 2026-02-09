from typing import Any
from app.vectorstore.retrieval import simple_retrieval
from app.llm.gemini_client import call_llm_sync, is_gemini_available


def run_rag(query: str, meeting_id: str | None = None) -> dict[str, Any]:
    docs = simple_retrieval(query, meeting_id)
    if not is_gemini_available():
        return {"answer": "LLM is not configured. Please set Gemini/Groq API key.", "citations": docs}
    context = "\n".join(str(doc) for doc in docs) if docs else "No relevant documents."
    prompt = f"""Question: {query}

Context:
{context}

Requirements:
- Respond concisely in English.
- Use ONLY information from Context.
- If evidence is insufficient, say so clearly."""
    answer = call_llm_sync(prompt)
    return {"answer": answer, "citations": docs}
