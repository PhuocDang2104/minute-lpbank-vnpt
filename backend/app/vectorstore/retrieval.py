from typing import List, Dict, Any
from app.vectorstore.pgvector_client import PgVectorClient
from app.vectorstore.light_rag import LightRAGRetriever


def simple_retrieval(query: str, meeting_id: str | None = None):
    client = PgVectorClient()
    results = client.search(query)
    for hit in results:
        hit['meeting_id'] = meeting_id
    return results


def light_rag_retrieval(question: str, meeting_id: str | None = None, project_id: str | None = None, topic_id: str | None = None) -> List[Dict[str, Any]]:
    retriever = LightRAGRetriever()
    return retriever.retrieve(question=question, meeting_id=meeting_id, project_id=project_id, topic_id=topic_id)
