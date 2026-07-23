import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.document_chunk import DocumentChunk
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_base import KnowledgeBase
from app.services.query_service import QueryService

logger = logging.getLogger("app.services.keyword_service")


class KeywordService:
    """
    Module 1: Keyword Search Engine
    Provides BM25-style keyword search functionality over document chunks in SQL.
    Supports tokenization, stop words removal, and exact match score boosting.
    """

    @staticmethod
    def search(
        db: Session,
        query: str,
        workspace_id: int,
        knowledge_base_id: List[int] = None,
        top_k: int = 10,
        user_id: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Scans chunk text for matching keyword tokens and assigns a keyword relevance score.
        Boosts exact query matches.
        """
        keywords = QueryService.extract_keywords(query)
        if not keywords:
            return []

        # Resolve manager/owner status for BM25 search
        is_manager = False
        if user_id:
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if user.company_role in ["OWNER", "ADMIN"]:
                    is_manager = True
                else:
                    from app.models.workspace_member import WorkspaceMember
                    member = db.query(WorkspaceMember).filter(
                        WorkspaceMember.workspace_id == workspace_id,
                        WorkspaceMember.user_id == user_id,
                        WorkspaceMember.is_active == True
                    ).first()
                    if member and member.workspace_role == "MANAGER":
                        is_manager = True

        # Prepare base query filtering by workspace and document status
        base_query = (
            db.query(DocumentChunk)
            .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
            .join(KnowledgeBase, KnowledgeDocument.knowledge_base_id == KnowledgeBase.id)
            .filter(
                KnowledgeBase.workspace_id == workspace_id,
                KnowledgeBase.deleted_at.is_(None),
                KnowledgeDocument.deleted_at.is_(None),
                KnowledgeDocument.status == "Completed",
                DocumentChunk.embedding_status == "Completed",
            )
        )

        if not is_manager and user_id:
            from sqlalchemy import or_
            base_query = base_query.filter(
                or_(
                    KnowledgeDocument.visibility == "WORKSPACE",
                    KnowledgeDocument.uploaded_by == user_id
                )
            )

        if knowledge_base_id:
            base_query = base_query.filter(KnowledgeBase.id.in_(knowledge_base_id))

        chunks = base_query.all()
        scored_results = []

        query_lower = query.lower().strip()

        for chunk in chunks:
            chunk_text_lower = chunk.text.lower()
            score = 0.0

            # 1. Exact match boost
            if query_lower in chunk_text_lower:
                score += 1.5

            # 2. Term frequency matching (BM25 token scanning simulation)
            for word in keywords:
                word_lower = word.lower()
                count = chunk_text_lower.count(word_lower)
                if count > 0:
                    # Logarithmic scale for term frequency saturation
                    import math
                    score += (count / (count + 1.5)) * 1.0

            if score > 0.0:
                scored_results.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "score": round(score, 4),
                    "page": chunk.page,
                    "section": chunk.section,
                    "token_count": chunk.token_count,
                    "chunk_index": chunk.chunk_index,
                })

        # Sort descending by score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
