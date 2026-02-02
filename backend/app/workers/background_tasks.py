from app.vectorstore.ingestion.pipelines import ingest_path


def enqueue_background_task(task: str):
    print(f"enqueue task: {task}")


def warmup_embeddings(sample_path: str):
    ingest_path(sample_path)