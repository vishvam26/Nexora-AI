from abc import ABC, abstractmethod
from typing import List


class EmbeddingInterface(ABC):
    """
    Interface for text embedding vector generation (OpenAI, Gemini, Voyage, Jina, offline Transformers).
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector list of float dimensions for a single text chunk.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embedding vectors in batch.
        """
        pass
