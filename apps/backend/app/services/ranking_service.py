import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.utils.token_counter import count_tokens

logger = logging.getLogger("app.services.ranking_service")

# Reranking weight constants
W_SIMILARITY = 0.70
W_IMPORTANCE = 0.15
W_FRESHNESS = 0.10
W_PINNED = 0.05

# Freshness decay: documents older than this many days score 0 on freshness
FRESHNESS_MAX_DAYS = 365


class RankingService:
    """
    Multi-factor reranking engine for RAG retrieved chunks.

    Ranking formula:
        score = 0.70 × similarity + 0.15 × importance + 0.10 × freshness + 0.05 × pinned

    Also handles:
    - Deduplication by content hash
    - Token budget enforcement (drop lowest-ranked chunks that exceed budget)
    """

    @staticmethod
    def rerank(
        chunks: List[Dict[str, Any]],
        doc_metadata: Dict[int, Dict[str, Any]],
        max_context_tokens: int = 4000,
        enable_reranking: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Input chunks format: [{chunk_id, document_id, text, score, page, section, token_count, ...}]
        doc_metadata: {doc_id: {filename, kb_title, created_at}}

        Returns reranked, deduplicated, token-budget-enforced chunk list.
        """
        if not chunks:
            return []

        # Step 1: Deduplicate by text content hash
        seen_hashes = set()
        unique_chunks = []
        for chunk in chunks:
            text_hash = hashlib.md5(chunk["text"].encode("utf-8", errors="ignore")).hexdigest()
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_chunks.append(chunk)
            else:
                logger.debug(f"Duplicate chunk removed: chunk_id={chunk.get('chunk_id')}")

        if not enable_reranking:
            # Sort by raw similarity only
            unique_chunks.sort(key=lambda c: c.get("score", 0), reverse=True)
            return RankingService._apply_token_budget(unique_chunks, max_context_tokens)

        # Step 2: Compute composite score for each chunk
        now = datetime.now(timezone.utc)
        scored = []
        for chunk in unique_chunks:
            doc_id = chunk.get("document_id", 0)
            meta = doc_metadata.get(doc_id, {})

            similarity = float(chunk.get("score", 0))
            importance = RankingService._importance_score(chunk)
            freshness = RankingService._freshness_score(meta.get("created_at"), now)
            pinned = 0.0  # placeholder for future pinned document feature

            composite = (
                W_SIMILARITY * similarity
                + W_IMPORTANCE * importance
                + W_FRESHNESS * freshness
                + W_PINNED * pinned
            )

            scored.append({
                **chunk,
                "composite_score": round(composite, 4),
                "doc_filename": meta.get("filename", "Unknown"),
                "kb_title": meta.get("kb_title", "Unknown KB"),
            })

        # Step 3: Sort descending by composite score
        scored.sort(key=lambda c: c["composite_score"], reverse=True)

        # Step 4: Apply token budget
        return RankingService._apply_token_budget(scored, max_context_tokens)

    @staticmethod
    def _importance_score(chunk: Dict[str, Any]) -> float:
        """
        Estimates chunk importance based on:
        - Position (earlier chunks in doc are more important)
        - Token density (longer chunks with more content rank higher)
        Returns value in [0, 1].
        """
        chunk_index = chunk.get("chunk_index", 0) if "chunk_index" in chunk else 0
        token_count = chunk.get("token_count", 50)

        # Prefer earlier chunks (index 0 = 1.0, decays with position)
        position_score = max(0.0, 1.0 - (chunk_index * 0.05))

        # Prefer substantive chunks (>= 100 tokens = full score)
        density_score = min(1.0, token_count / 100.0)

        return round((position_score * 0.6 + density_score * 0.4), 4)

    @staticmethod
    def _freshness_score(created_at: Optional[Any], now: datetime) -> float:
        """
        Documents created more recently score higher.
        Returns value in [0, 1]: 1.0 = today, 0.0 = older than FRESHNESS_MAX_DAYS.
        """
        if not created_at:
            return 0.5  # neutral if no timestamp

        try:
            if isinstance(created_at, str):
                from datetime import datetime as dt
                created_at = dt.fromisoformat(created_at)

            # Ensure timezone awareness
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            age_days = (now - created_at).days
            score = max(0.0, 1.0 - (age_days / FRESHNESS_MAX_DAYS))
            return round(score, 4)
        except Exception:
            return 0.5

    @staticmethod
    def _apply_token_budget(
        chunks: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Greedily accepts chunks from the top of the ranked list
        until the token budget is exhausted.
        """
        accepted = []
        total_tokens = 0

        for chunk in chunks:
            chunk_tokens = chunk.get("token_count", count_tokens(chunk.get("text", "")))
            if total_tokens + chunk_tokens <= max_tokens:
                accepted.append(chunk)
                total_tokens += chunk_tokens
            else:
                logger.debug(
                    f"Chunk dropped (budget): chunk_id={chunk.get('chunk_id')}, "
                    f"tokens={chunk_tokens}, budget_remaining={max_tokens - total_tokens}"
                )

        logger.info(
            f"Token budget: used={total_tokens}/{max_tokens}, "
            f"accepted={len(accepted)}, dropped={len(chunks) - len(accepted)}"
        )
        return accepted
