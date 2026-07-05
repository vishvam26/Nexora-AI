from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.knowledge_document import KnowledgeDocument


class KnowledgeDocumentRepository:

    @staticmethod
    def create(db: Session, knowledge_base_id: int, uploaded_by: int, **kwargs) -> KnowledgeDocument:
        doc = KnowledgeDocument(knowledge_base_id=knowledge_base_id, uploaded_by=uploaded_by, **kwargs)
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_by_id(db: Session, doc_id: int) -> Optional[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.deleted_at.is_(None)
        ).first()

    @staticmethod
    def list_by_knowledge_base(db: Session, knowledge_base_id: int) -> List[KnowledgeDocument]:
        return db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeDocument.deleted_at.is_(None)
        ).order_by(KnowledgeDocument.created_at.desc()).all()

    @staticmethod
    def update_status(db: Session, doc: KnowledgeDocument, status: str) -> KnowledgeDocument:
        doc.status = status
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def update(db: Session, doc: KnowledgeDocument, **kwargs) -> KnowledgeDocument:
        for k, v in kwargs.items():
            setattr(doc, k, v)
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def soft_delete(db: Session, doc: KnowledgeDocument) -> None:
        from datetime import datetime
        doc.deleted_at = datetime.utcnow()
        db.commit()
