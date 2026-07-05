import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.embedding.embedding_service import EmbeddingService
from app.services.vector_store.memory_vector_store import MemoryVectorStore

logger = logging.getLogger("app.services.retrieval_service")

_embedder = EmbeddingService()
_vector_store = MemoryVectorStore()


class RetrievalService:
    """
    Performs similarity search against document chunks for a given query.
    Returns ranked list of relevant text chunks to be injected into AI context.
    """

    @staticmethod
    def retrieve(
        db: Session,
        query: str,
        workspace_id: int,
        knowledge_base_id: Optional[int] = None,
        top_k: int = 5,
        threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        1. Embeds the query.
        2. Searches vector store with optional KB and workspace filters.
        3. Fetches matching chunk text from database.
        4. Returns ranked chunk list with score and metadata.
        """
        query_embedding = _embedder.embed_text(query)

        # Build metadata filters
        filters: Dict[str, Any] = {"workspace_id": workspace_id}
        if knowledge_base_id:
            filters["knowledge_base_id"] = knowledge_base_id

        # Vector similarity search
        matches = _vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold,
            filters=filters,
        )

        if not matches:
            return []

        # Enrich with DB chunk text
        results = []
        for match in matches:
            chunk = DocumentChunkRepository.get_by_id(db, match["chunk_id"])
            if chunk:
                results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "score": round(match["score"], 4),
                    "page": chunk.page,
                    "section": chunk.section,
                    "token_count": chunk.token_count,
                })

        return results
