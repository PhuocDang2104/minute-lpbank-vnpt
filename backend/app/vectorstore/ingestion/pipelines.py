from app.vectorstore.pgvector_client import PgVectorClient
from app.vectorstore.ingestion import loaders


def ingest_path(path: str):
    client = PgVectorClient()
    text = loaders.load_text(path)
    client.upsert([text])