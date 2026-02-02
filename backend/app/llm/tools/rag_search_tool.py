from typing import Any, Dict, List
from app.vectorstore.retrieval import light_rag_retrieval


def rag_retrieve(question: str, meeting_id: str | None = None, topic_id: str | None = None, project_id: str | None = None) -> List[Dict[str, Any]]:
    """LightRAG-lite retriever with bucket priority: meeting > project/topic > global."""
    return light_rag_retrieval(question=question, meeting_id=meeting_id, project_id=project_id, topic_id=topic_id)
