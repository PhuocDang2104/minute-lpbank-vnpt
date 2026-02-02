"""
Seed mock LPBank documents into pgvector (stub) and LightRAG dataset.
Run manually if you want to populate local vector store.
"""
from app.vectorstore.pgvector_client import PgVectorClient
from app.vectorstore.light_rag import SEED_DOCS


def seed():
    client = PgVectorClient()
    texts = [f"{d.title} :: {d.snippet}" for d in SEED_DOCS]
    client.upsert(texts)
    print(f"Seeded {len(texts)} LPBank mock docs into pgvector stub.")


if __name__ == "__main__":
    seed()
