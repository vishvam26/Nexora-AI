import time
import logging
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session

from app.services.query_classifier import QueryClassifier
from app.services.context_strategy import ContextStrategyEngine
from app.services.intent_service import IntentService
from app.services.hybrid_search_service import HybridSearchService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.ranking_service import RankingService
from app.services.context_service import ContextService
from app.services.compression_service import CompressionService
from app.services.citation_service import CitationEngine
from app.services.retrieval_cache import RetrievalCache
from app.repositories.knowledge_search_repository import KnowledgeSearchRepository
from app.utils.similarity import compute_jaccard_similarity
from app.models.retrieval_log import RetrievalLog
from app.schemas.retrieval import RAGContext, RetrievalMetrics, RetrievedChunk

logger = logging.getLogger("app.services.adaptive_retrieval_service")


class AdaptiveRetrievalService:
    """
    Module 1: Adaptive Retrieval Engine
    Uses intent classification and dynamic context strategies to optimize chunk parameters (Dynamic Top-K),
    remove near-duplicates, prioritize sources, run cache checks, and return formatted contexts.
    """

    @staticmethod
    def retrieve_context(
        db: Session,
        user_query: str,
        workspace_id: int,
        knowledge_base_id: Optional[Union[int, List[int]]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.1,
        max_context_tokens: int = 4000,
        enable_reranking: bool = True,
        vector_weight: float = 0.70,
        keyword_weight: float = 0.30,
        graph_max_depth: int = 2,
        cache_expiry_seconds: int = 300,
        duplicate_threshold: float = 0.90,
    ) -> RAGContext:
        """
        Orchestrates classified RAG routing, dynamically resizing parameters and caching.
        """
        start_time = time.monotonic()

        # 1. Cache Check
        cached = RetrievalCache.get(workspace_id, user_query, expiry_seconds=cache_expiry_seconds)
        if cached:
            return cached

        try:
            # 2. Query Classification
            classification = QueryClassifier.classify(user_query)
            category = classification["category"]
            intent_confidence = classification["confidence"]

            # 3. Context Strategy Routing
            strategy = ContextStrategyEngine.determine_strategy(category)
            logger.info(f"Adaptive RAG: Category={category} | Intent Confidence={intent_confidence} | Strategy={strategy}")

            if strategy == "No Retrieval":
                empty_res = AdaptiveRetrievalService._empty_context(start_time, category, strategy)
                return empty_res

            # 4. Dynamic Top-K Adjustment
            dynamic_k = top_k
            if category in ["Greeting", "Summarization"]:
                dynamic_k = 2
            elif category in ["Coding", "Debugging"]:
                dynamic_k = 12  # Large contexts for debugging

            # 5. Hybrid Search Retrieval
            expanded_terms = IntentService.expand_query(user_query)
            search_query = " ".join(expanded_terms)

            raw_hits = HybridSearchService.search(
                db=db,
                query=search_query,
                workspace_id=workspace_id,
                knowledge_base_id=knowledge_base_id,
                vector_weight=vector_weight,
                keyword_weight=keyword_weight,
                top_k=dynamic_k * 2,
                threshold=similarity_threshold
            )

            if not raw_hits:
                return AdaptiveRetrievalService._empty_context(start_time, category, strategy)

            # 6. Near-Duplicate Chunk Filtering (Module 6)
            unique_hits = []
            for hit in raw_hits:
                is_duplicate = False
                for existing in unique_hits:
                    sim = compute_jaccard_similarity(hit["text"], existing["text"])
                    if sim >= duplicate_threshold:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_hits.append(hit)

            # 7. Knowledge Graph Connection fetching
            related_concepts = []
            if strategy == "Knowledge Graph":
                related_concepts = KnowledgeGraphService.get_related_concepts(
                    db=db,
                    workspace_id=workspace_id,
                    seed_terms=expanded_terms,
                    max_depth=graph_max_depth
                )
            graph_context_str = ", ".join(related_concepts) if related_concepts else ""

            # 8. Fetch document metadata for ranking & source prioritization
            doc_ids = {hit["document_id"] for hit in unique_hits}
            doc_metadata = KnowledgeSearchRepository.get_bulk_document_metadata(db, list(doc_ids))

            # 9. Reranking
            ranked_hits = RankingService.rerank(
                chunks=unique_hits,
                doc_metadata=doc_metadata,
                max_context_tokens=max_context_tokens * 2,
                enable_reranking=enable_reranking
            )

            # 10. Source Diversity Filter
            diverse_hits = []
            doc_count: Dict[int, int] = {}
            for hit in ranked_hits:
                doc_id = hit["document_id"]
                count = doc_count.get(doc_id, 0)
                if count < 2:
                    diverse_hits.append(hit)
                    doc_count[doc_id] = count + 1

            # 11. Context Compression (Module 5)
            compressed_hits = CompressionService.compress_chunks(diverse_hits, max_tokens=max_context_tokens)

            # 12. Token Budget trimming
            final_hits = RankingService._apply_token_budget(compressed_hits, max_context_tokens)

            # 13. Citation compilation (Module 9)
            citations = CitationEngine.generate_citations(final_hits)
            citations_block = CitationEngine.format_citations_block(citations)

            # 14. Confidence Score (Module 8 & 10)
            avg_similarity = sum(h.get("score", 0.0) for h in final_hits) / len(final_hits) if final_hits else 0.0
            search_confidence = min(1.0, len(final_hits) / (dynamic_k or 1))
            retrieval_confidence = min(1.0, avg_similarity)
            confidence_score = round(0.5 * avg_similarity + 0.3 * search_confidence + 0.2 * retrieval_confidence, 4)

            # 15. Format final context string
            formatted_context = ContextService.format_context(final_hits)
            if citations_block:
                formatted_context += "\n" + citations_block

            # 16. Log retrieval analytics
            latency_ms = (time.monotonic() - start_time) * 1000
            dropped = len(raw_hits) - len(final_hits)

            doc_ids_list = list(doc_ids) if 'doc_ids' in locals() and doc_ids else []
            log_entry = RetrievalLog(
                query=user_query,
                latency_ms=int(latency_ms),
                top_k=top_k,
                returned_document_ids=doc_ids_list
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

            result_context = RAGContext(
                formatted_context=formatted_context,
                chunks_used=chunk_responses,
                metrics=metrics,
                has_knowledge=ContextService.has_results(final_hits),
                graph_context=graph_context_str,
                confidence_score=confidence_score
            )

            # Save in Cache
            RetrievalCache.set(workspace_id, user_query, result_context)
            return result_context

        except Exception as exc:
            logger.error(f"Adaptive RAG Pipeline Error: {exc}", exc_info=True)
            return AdaptiveRetrievalService._empty_context(start_time, "Fallback", "Fallback")

    @staticmethod
    def _empty_context(start_time: float, intent: str, strategy: str) -> RAGContext:
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
