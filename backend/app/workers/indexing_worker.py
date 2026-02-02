from app.vectorstore.ingestion.pipelines import ingest_path


def run_index_job(path: str):
    ingest_path(path)
    return {"status": "indexed", "path": path}