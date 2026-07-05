import logging
import hashlib
import random
from typing import List
from app.services.embedding.embedding_interface import EmbeddingInterface

logger = logging.getLogger("app.services.embedding.embedding_service")


class EmbeddingService(EmbeddingInterface):
    """
    RAG Embedding Service coordinate generating document chunk vectors.
    """

    def __init__(self, provider: str = "mock", dimensions: int = 1536):
        self.provider = provider
        self.dimensions = dimensions

    def embed_text(self, text: str) -> List[float]:
        """
        Generates a deterministic float vector based on chunk hash.
        This provides offline similarity calculation fallback compatibility.
        """
        # Deteministic mock vector generation using md5 hash of text
        text_bytes = text.encode("utf-8", errors="ignore")
        seed = int(hashlib.md5(text_bytes).hexdigest(), 16) % (2**32)
        
        # Initialize a deterministic random seed generator
        rng = random.Random(seed)
        
        # Generate normalized float values
        vector = [rng.uniform(-1.0, 1.0) for _ in range(self.dimensions)]
        
        # Normalize vector length to 1.0 for cosine similarity calculations
        sq_sum = sum(x * x for x in vector)
        magnitude = sq_sum ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Processes list of text chunks in batch.
        """
        return [self.embed_text(txt) for txt in texts]

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Named alias for query-time embedding generation.
        Always uses the same model and dimensions as document indexing,
        ensuring vector space compatibility.
        """
        return self.embed_text(query)

