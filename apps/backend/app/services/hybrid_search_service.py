import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.vector_store.memory_vector_store import MemoryVectorStore
from app.services.embedding.embedding_service import EmbeddingService
from app.services.keyword_service import KeywordService
from app.repositories.document_chunk_repository import DocumentChunkRepository

logger = logging.getLogger("app.services.hybrid_search_service")

_embedder = EmbeddingService()
_vector_store = MemoryVectorStore()


class HybridSearchService:
    """
    Module 2: Hybrid Search Merger
    Executes Vector Search (Semantic) & Keyword Search (Lexical) in parallel,
    normalizes scores, merges them using weights, and returns unified top results.
    """

    @staticmethod
    def search(
        db: Session,
        query: str,
        workspace_id: int,
        knowledge_base_id: Optional[int] = None,
        vector_weight: float = 0.70,
        keyword_weight: float = 0.30,
        top_k: int = 10,
        threshold: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        Runs both searches, normalizes their scores, merges items, and returns top K.
        """
        kb_filter = [knowledge_base_id] if knowledge_base_id else None

        # 1. Lexical Keyword Search
        keyword_results = KeywordService.search(
            db=db,
            query=query,
            workspace_id=workspace_id,
            knowledge_base_id=kb_filter,
            top_k=top_k * 2,
        )

        # 2. Semantic Vector Search
        query_embedding = _embedder.generate_query_embedding(query)
        filters = {"workspace_id": workspace_id}
        if knowledge_base_id:
            filters["knowledge_base_id"] = knowledge_base_id

        vector_matches = _vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,
            threshold=threshold,
            filters=filters,
        )

        vector_results = []
        for match in vector_matches:
            chunk = DocumentChunkRepository.get_by_id(db, match["chunk_id"])
            if chunk:
                vector_results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "score": match["score"],
                    "page": chunk.page,
                    "section": chunk.section,
                    "token_count": chunk.token_count,
                    "chunk_index": chunk.chunk_index,
                })

        # 3. Normalize score utilities
        def normalize_results(results: List[Dict[str, Any]]) -> Dict[int, float]:
            if not results:
                return {}
            max_score = max(r["score"] for r in results)
            min_score = min(r["score"] for r in results)
            diff = max_score - min_score
            if diff == 0:
                return {r["chunk_id"]: 1.0 for r in results}
            return {r["chunk_id"]: (r["score"] - min_score) / diff for r in results}

        norm_vector = normalize_results(vector_results)
        norm_keyword = normalize_results(keyword_results)

        # Map details
        chunk_details: Dict[int, Dict[str, Any]] = {}
        for r in vector_results + keyword_results:
            chunk_details[r["chunk_id"]] = r

        # 4. Merge results
        merged_scores: Dict[int, float] = {}
        all_chunk_ids = set(norm_vector.keys()).union(set(norm_keyword.keys()))

        for cid in all_chunk_ids:
            v_score = norm_vector.get(cid, 0.0)
            k_score = norm_keyword.get(cid, 0.0)
            merged_scores[cid] = (vector_weight * v_score) + (keyword_weight * k_score)

        # Compile and sort
        merged_results = []
        for cid, combined_score in merged_scores.items():
            details = chunk_details[cid]
            merged_results.append({
                **details,
                "score": round(combined_score, 4),
            })

        merged_results.sort(key=lambda x: x["score"], reverse=True)
        return merged_results[:top_k]
