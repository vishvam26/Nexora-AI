from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStoreInterface(ABC):
    """
    Interface for Vector Store providers (PgVector, Qdrant, Pinecone, Weaviate, Milvus, Chroma).
    """

    @abstractmethod
    def add(self, chunk_id: int, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """
        Adds a single embedding vector to the store.
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the most similar chunk matches with optional metadata filters.
        Returns list of dicts with keys: chunk_id, score, metadata.
        """
        pass

    @abstractmethod
    def delete(self, chunk_id: int) -> None:
        """
        Removes a chunk embedding from the store.
        """
        pass
