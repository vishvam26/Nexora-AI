import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("app.services.retrieval_cache")

# Fast Local memory cache (key = workspace_id:query, value = (rag_context, expiry_timestamp))
_CACHE: Dict[str, tuple] = {}


class RetrievalCache:
    """
    Module 11: Cache Layer
    Caches RAG context results for repeat queries within workspaces to avoid redundant search latency.
    """

    @staticmethod
    def get(workspace_id: int, query: str, expiry_seconds: int = 300) -> Optional[Any]:
        """
        Retrieves cached RAGContext if valid and not expired.
        """
        cache_key = f"{workspace_id}:{query.lower().strip()}"
        if cache_key in _CACHE:
            context, timestamp = _CACHE[cache_key]
            if time.time() - timestamp < expiry_seconds:
                logger.info(f"RAG: Cache Hit for key: {cache_key}")
                return context
            else:
                # Expiry clean up
                _CACHE.pop(cache_key, None)
        return None

    @staticmethod
    def set(workspace_id: int, query: str, context: Any) -> None:
        """
        Saves RAGContext to local memory cache.
        """
        cache_key = f"{workspace_id}:{query.lower().strip()}"
        _CACHE[cache_key] = (context, time.time())
