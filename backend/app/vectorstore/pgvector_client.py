from typing import List


class PgVectorClient:
    def __init__(self, connection: str | None = None) -> None:
        self.connection = connection or 'postgresql+psycopg2://meetmate:meetmate@localhost:5432/meetmate'

    def upsert(self, texts: List[str]) -> None:
        # Stub: pretend to store embeddings
        for text in texts:
            print(f"[pgvector] upsert: {text[:32]}")

    def search(self, query: str) -> List[dict]:
        return [{"source": "stub", "snippet": f"match for {query}"}]