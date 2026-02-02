"""
Simple local embedding server (FastAPI) using sentence-transformers.

Usage:
  export MODEL_NAME="Alibaba-NLP/gte-small"   # optional, default gte-small
  uvicorn backend.local_embeddings.server:app --host 0.0.0.0 --port 8001

API:
  GET /health           -> {"status": "ok"}
  POST /embed           -> {"embeddings": [[...], ...]}
    body: {"texts": ["...", "..."], "normalize": true}
"""
import os
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer


MODEL_NAME = os.environ.get("MODEL_NAME", "Alibaba-NLP/gte-small")

app = FastAPI(title="Local Embedding Server", version="1.0.0")
model = SentenceTransformer(MODEL_NAME)


class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., description="List of input texts")
    normalize: bool = Field(default=True, description="Whether to L2 normalize embeddings")


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts must not be empty")
    vectors = model.encode(req.texts, normalize_embeddings=req.normalize).tolist()
    return EmbedResponse(embeddings=vectors)
