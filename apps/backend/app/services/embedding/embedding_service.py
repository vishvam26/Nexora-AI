import os
import sqlite3
import json
import hashlib
import logging
from typing import List, Optional, Tuple

from app.config import settings
from app.services.embedding.embedding_interface import EmbeddingInterface

logger = logging.getLogger("app.services.embedding.embedding_service")

# Lazy loading of sentence_transformers to save start time and fallback gracefully
_model_instance = None
_sentence_transformers_available = False

try:
    from sentence_transformers import SentenceTransformer
    import torch
    _sentence_transformers_available = True
except ImportError:
    SentenceTransformer = None
    torch = None


class SQLiteEmbeddingCache:
    """
    Persistent SQLite database cache for generated document chunk embeddings.
    Avoids re-computing identical chunks through SHA-256 caching.
    """
    def __init__(self, db_path: str = "embedding_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS embedding_cache (
                        chunk_hash TEXT PRIMARY KEY,
                        vector TEXT NOT NULL
                    )
                    """
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize embedding cache DB: {e}")

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        h = self._hash(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT vector FROM embedding_cache WHERE chunk_hash = ?", (h,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            logger.warning(f"Error reading from embedding cache: {e}")
        return None

    def set(self, text: str, vector: List[float]):
        h = self._hash(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO embedding_cache (chunk_hash, vector) VALUES (?, ?)",
                    (h, json.dumps(vector))
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Error writing to embedding cache: {e}")

    def set_batch(self, items: List[Tuple[str, List[float]]]):
        if not items:
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO embedding_cache (chunk_hash, vector) VALUES (?, ?)",
                    [(self._hash(text), json.dumps(vec)) for text, vec in items]
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Error batch writing to embedding cache: {e}")


class EmbeddingService(EmbeddingInterface):
    """
    RAG Embedding Service.
    Generates real float vectors using sentence-transformers with caching and GPU batching.
    Gracefully falls back to deterministic mock vectors if sentence-transformers is missing.
    """

    def __init__(self, provider: str = "local", dimensions: int = 384):
        self.provider = provider
        self.dimensions = dimensions
        self.cache = SQLiteEmbeddingCache()
        self._init_model()

    def _init_model(self):
        global _model_instance
        if not _sentence_transformers_available:
            logger.warning(
                "sentence-transformers not available. Falling back to deterministic Mock Embeddings."
            )
            return

        if _model_instance is None:
            try:
                model_name = settings.EMBEDDING_MODEL
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Loading SentenceTransformer: '{model_name}' on device='{device}'")
                
                # Check setting export path overrides
                if settings.HF_HOME:
                    os.environ["HF_HOME"] = settings.HF_HOME

                _model_instance = SentenceTransformer(model_name, device=device)
                
                # Retrieve actual dimension size of model configuration
                try:
                    self.dimensions = _model_instance.get_sentence_embedding_dimension()
                    logger.info(f"Loaded embedding model with dimensions: {self.dimensions}")
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed to load sentence-transformer model: {e}. Using mock mode.")

    def embed_text(self, text: str) -> List[float]:
        """
        Generates a vector embedding for a single text chunk, checking cache first.
        """
        cached = self.cache.get(text)
        if cached:
            return cached

        # Generate new embedding
        if _model_instance is not None:
            try:
                vector = _model_instance.encode(text, convert_to_numpy=True).tolist()
                self.cache.set(text, vector)
                return vector
            except Exception as e:
                logger.error(f"Failed to generate real embedding: {e}")

        # Mock Fallback
        vector = self._mock_embedding(text)
        self.cache.set(text, vector)
        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a batch of text chunks, leveraging cache and parallel GPU processing.
        """
        results = [None] * len(texts)
        missing_indices = []
        missing_texts = []

        # 1. Fetch cached items
        for i, txt in enumerate(texts):
            cached = self.cache.get(txt)
            if cached:
                results[i] = cached
            else:
                missing_indices.append(i)
                missing_texts.append(txt)

        # 2. Compute missing vectors in a batch
        if missing_texts:
            if _model_instance is not None:
                try:
                    logger.info(f"Computing real embeddings batch for {len(missing_texts)} missing chunks")
                    vectors = _model_instance.encode(
                        missing_texts, 
                        batch_size=32, 
                        show_progress_bar=False, 
                        convert_to_numpy=True
                    ).tolist()
                    
                    # Write to cache and merge results
                    cache_items = []
                    for idx, text, vec in zip(missing_indices, missing_texts, vectors):
                        results[idx] = vec
                        cache_items.append((text, vec))
                    self.cache.set_batch(cache_items)
                except Exception as e:
                    logger.error(f"Batch real embedding failed: {e}. Falling back to individual mock.")
            
            # Fallback to mock for any remaining unresolved items
            cache_items = []
            for idx in missing_indices:
                if results[idx] is None:
                    txt = texts[idx]
                    vec = self._mock_embedding(txt)
                    results[idx] = vec
                    cache_items.append((txt, vec))
            if cache_items:
                self.cache.set_batch(cache_items)

        return results

    def generate_query_embedding(self, query: str) -> List[float]:
        return self.embed_text(query)

    def _mock_embedding(self, text: str) -> List[float]:
        """
        Fallback mock embedding generation matching original offline deterministic logic.
        """
        text_bytes = text.encode("utf-8", errors="ignore")
        seed = int(hashlib.md5(text_bytes).hexdigest(), 16) % (2**32)
        import random
        rng = random.Random(seed)
        vector = [rng.uniform(-1.0, 1.0) for _ in range(self.dimensions)]
        sq_sum = sum(x * x for x in vector)
        magnitude = sq_sum ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]
        return vector
