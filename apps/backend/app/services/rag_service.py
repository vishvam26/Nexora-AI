import time
import logging
import math
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.services.intent_service import IntentService
from app.services.hybrid_search_service import HybridSearchService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.ranking_service import RankingService
from app.services.context_service import ContextService
from app.repositories.knowledge_search_repository import KnowledgeSearchRepository
from app.models.retrieval_log import RetrievalLog
from app.schemas.retrieval import RAGContext, RetrievalMetrics, RetrievedChunk

logger = logging.getLogger("app.services.rag_service")


class RAGService:
    """
    Orchestrates the full Advanced Hybrid RAG retrieval pipeline:

    1. Intent Detection  (IntentService.detect_intent)
    2. Query Expansion   (IntentService.expand_query)
    3. Hybrid Search     (HybridSearchService.search — Vector + BM25)
    4. Graph Expansion   (KnowledgeGraphService.get_related_concepts)
    5. DB Enrichment     (KnowledgeSearchRepository)
    6. Multi-Factor Reranking (RankingService.rerank)
    7. Diversity Filter  (Source diversity selection)
    8. Confidence Score calculation
    9. Log Retrieval Metrics to Database (RetrievalLog)
    """

    @staticmethod
    def retrieve_context(
        db: Session,
        user_query: str,
        workspace_id: int,
        knowledge_base_id: Optional[int] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.1,
        max_context_tokens: int = 4000,
        enable_reranking: bool = True,
        vector_weight: float = 0.70,
        keyword_weight: float = 0.30,
        graph_max_depth: int = 2,
        user_id: Optional[int] = None,
    ) -> RAGContext:
        """
        Runs advanced RAG pipeline, expanding query concepts, doing hybrid search,
        calculating confidence, and maintaining source diversity.
        """
        start_time = time.monotonic()

        try:
            # 1. Intent Detection
            intent = IntentService.detect_intent(user_query)

            # 2. Query Expansion
            expanded_terms = IntentService.expand_query(user_query)
            search_query = " ".join(expanded_terms)

            # 3. Hybrid Search (Vector + Keyword)
            raw_hits = HybridSearchService.search(
                db=db,
                query=search_query,
                workspace_id=workspace_id,
                knowledge_base_id=knowledge_base_id,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight,
                top_k=top_k * 2,
                threshold=similarity_threshold,
                user_id=user_id,
            )

            if not raw_hits:
                return RAGService._empty_context(start_time, intent)

            # 4. Knowledge Graph Expansion
            related_concepts = KnowledgeGraphService.get_related_concepts(
                db=db,
                workspace_id=workspace_id,
                seed_terms=expanded_terms,
                max_depth=graph_max_depth
            )
            graph_context_str = ", ".join(related_concepts) if related_concepts else ""

            # 5. DB Enrichment & Metadata Gathering
            doc_ids = {hit["document_id"] for hit in raw_hits}
            doc_metadata = KnowledgeSearchRepository.get_bulk_document_metadata(db, list(doc_ids))

            # 6. Reranking
            ranked_hits = RankingService.rerank(
                chunks=raw_hits,
                doc_metadata=doc_metadata,
                max_context_tokens=max_context_tokens * 2,
                enable_reranking=enable_reranking
            )

            # 7. Diversity Filter (Module 9: Maximum 2 chunks from the same document)
            diverse_hits = []
            doc_count: Dict[int, int] = {}
            for hit in ranked_hits:
                doc_id = hit["document_id"]
                count = doc_count.get(doc_id, 0)
                if count < 2:
                    diverse_hits.append(hit)
                    doc_count[doc_id] = count + 1

            # 8. Token budget limit
            final_hits = RankingService._apply_token_budget(diverse_hits, max_context_tokens)

            # 9. Confidence Score Calculation (Module 10)
            avg_similarity = sum(h.get("score", 0.0) for h in final_hits) / len(final_hits) if final_hits else 0.0
            search_confidence = min(1.0, len(final_hits) / (top_k or 1))
            retrieval_confidence = min(1.0, avg_similarity)

            confidence_score = round(0.5 * avg_similarity + 0.3 * search_confidence + 0.2 * retrieval_confidence, 4)

            # 10. Format Context
            formatted_context = ContextService.format_context(final_hits)

            # 11. Logging analytics (Module 11)
            latency_ms = (time.monotonic() - start_time) * 1000
            dropped = len(raw_hits) - len(final_hits)

            log_entry = RetrievalLog(
                workspace_id=workspace_id,
                query=user_query,
                intent=intent,
                latency_ms=round(latency_ms, 2),
                confidence_score=confidence_score,
                chunks_retrieved=len(raw_hits),
                chunks_accepted=len(final_hits),
                chunks_rejected=dropped
            )
            db.add(log_entry)
            db.commit()

            metrics = RetrievalMetrics(
                latency_ms=round(latency_ms, 2),
                retrieved_count=len(final_hits),
                dropped_count=dropped,
                avg_similarity=round(avg_similarity, 4),
                used_fallback=False
            )

            chunk_responses = [
                RetrievedChunk(
                    chunk_id=c["chunk_id"],
                    document_id=c["document_id"],
                    text=c["text"],
                    score=c["score"],
                    composite_score=c.get("composite_score"),
                    page=c.get("page"),
                    section=c.get("section"),
                    token_count=c["token_count"],
                    doc_filename=c.get("doc_filename"),
                    kb_title=c.get("kb_title")
                )
                for c in final_hits
            ]

            return RAGContext(
                formatted_context=formatted_context,
                chunks_used=chunk_responses,
                metrics=metrics,
                has_knowledge=ContextService.has_results(final_hits),
                graph_context=graph_context_str,
                confidence_score=confidence_score
            )

        except Exception as exc:
            logger.error(f"Advanced RAG pipeline error: {exc}", exc_info=True)
            return RAGService._empty_context(start_time, "Fallback")

    @staticmethod
    def _empty_context(start_time: float, intent: str) -> RAGContext:
        latency_ms = (time.monotonic() - start_time) * 1000
        return RAGContext(
            formatted_context="",
            chunks_used=[],
            metrics=RetrievalMetrics(
                latency_ms=round(latency_ms, 2),
                retrieved_count=0,
                dropped_count=0,
                avg_similarity=0.0,
                used_fallback=True
            ),
            has_knowledge=False,
            graph_context="",
            confidence_score=0.0
        )
