from typing import List


class EmbeddingClient:
    def embed(self, texts: List[str]) -> list[list[float]]:
        # Stub embeddings with zeros
        return [[0.0 for _ in range(4)] for _ in texts]