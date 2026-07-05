import math
import logging
from typing import List, Dict, Any, Optional
from app.services.vector_store.vector_interface import VectorStoreInterface

logger = logging.getLogger("app.services.vector_store.memory_vector_store")


class MemoryVectorStore(VectorStoreInterface):
    """
    In-memory cosine-similarity vector store for standalone/development usage.
    Acts as default fallback when PgVector or external providers are not configured.
    
    Future: Replace with PgVector, Qdrant, Pinecone etc by swapping this implementation.
    """

    def __init__(self):
        # Store: {chunk_id: {"embedding": [...], "metadata": {...}}}
        self._store: Dict[int, Dict[str, Any]] = {}

    def add(self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]) -> None:
        self._store[chunk_id] = {"embedding": embedding, "metadata": metadata}
        logger.debug(f"Stored embedding for chunk_id={chunk_id}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns top_k nearest neighbours by cosine similarity.
        Optional metadata key-value filters are applied before similarity ranking.
        """
        results = []

        for chunk_id, record in self._store.items():
            # Apply optional metadata key-value filters
            if filters:
                meta = record.get("metadata", {})
                if not all(meta.get(k) == v for k, v in filters.items()):
                    continue

            score = self._cosine_similarity(query_embedding, record["embedding"])
            if score >= threshold:
                results.append({"chunk_id": chunk_id, "score": score, "metadata": record["metadata"]})

        # Sort descending by score, return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def delete(self, chunk_id: int) -> None:
        if chunk_id in self._store:
            del self._store[chunk_id]
            logger.debug(f"Deleted embedding for chunk_id={chunk_id}")

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Computes cosine similarity between two equal-length float vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
