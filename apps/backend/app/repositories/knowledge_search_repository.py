import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.document_chunk import DocumentChunk
from app.models.knowledge_document import KnowledgeDocument
from app.models.knowledge_base import KnowledgeBase

logger = logging.getLogger("app.repositories.knowledge_search_repository")


class KnowledgeSearchRepository:
    """
    Read-only repository for workspace-isolated chunk retrieval during RAG queries.
    Enforces security: never returns chunks from soft-deleted documents,
    inactive knowledge bases, or documents belonging to other workspaces.
    """

    @staticmethod
    def get_chunks_by_workspace(db: Session, workspace_id: int) -> List[DocumentChunk]:
        """
        Returns all embedded chunks scoped to a workspace.
        Excludes: soft-deleted documents, failed/pending chunks, deleted knowledge bases.
        """
        return (
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
            .all()
        )

    @staticmethod
    def get_chunks_by_knowledge_base(db: Session, kb_id: int) -> List[DocumentChunk]:
        """Returns all embedded chunks scoped to a single knowledge base."""
        return (
            db.query(DocumentChunk)
            .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
            .filter(
                KnowledgeDocument.knowledge_base_id == kb_id,
                KnowledgeDocument.deleted_at.is_(None),
                KnowledgeDocument.status == "Completed",
                DocumentChunk.embedding_status == "Completed",
            )
            .all()
        )

    @staticmethod
    def get_document_metadata(db: Session, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Returns lightweight document metadata used for reranking signals:
        - created_at (freshness)
        - filename / knowledge base name
        """
        doc = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.id == doc_id,
                KnowledgeDocument.deleted_at.is_(None),
            )
            .first()
        )
        if not doc:
            return None

        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == doc.knowledge_base_id).first()
        kb_title = kb.title if kb else "Unknown KB"

        return {
            "doc_id": doc.id,
            "filename": doc.filename,
            "kb_title": kb_title,
            "created_at": doc.created_at,
            "status": doc.status,
        }

    @staticmethod
    def get_bulk_document_metadata(
        db: Session, doc_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """Batch fetch document metadata for a list of doc_ids."""
        docs = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.id.in_(doc_ids),
                KnowledgeDocument.deleted_at.is_(None),
            )
            .all()
        )
        kb_ids = list({d.knowledge_base_id for d in docs})
        kbs = db.query(KnowledgeBase).filter(KnowledgeBase.id.in_(kb_ids)).all()
        kb_map = {kb.id: kb for kb in kbs}

        result: Dict[int, Dict[str, Any]] = {}
        for doc in docs:
            kb = kb_map.get(doc.knowledge_base_id)
            result[doc.id] = {
                "doc_id": doc.id,
                "filename": doc.filename,
                "kb_title": kb.title if kb else "Unknown KB",
                "created_at": doc.created_at,
            }
        return result
