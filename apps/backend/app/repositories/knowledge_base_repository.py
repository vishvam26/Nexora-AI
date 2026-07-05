from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:

    @staticmethod
    def create(db: Session, workspace_id: int, created_by: int, **kwargs) -> KnowledgeBase:
        kb = KnowledgeBase(workspace_id=workspace_id, created_by=created_by, **kwargs)
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def get_by_id(db: Session, kb_id: int) -> Optional[KnowledgeBase]:
        return db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.deleted_at.is_(None)
        ).first()

    @staticmethod
    def list_by_workspace(db: Session, workspace_id: int) -> List[KnowledgeBase]:
        return db.query(KnowledgeBase).filter(
            KnowledgeBase.workspace_id == workspace_id,
            KnowledgeBase.deleted_at.is_(None)
        ).order_by(KnowledgeBase.created_at.desc()).all()

    @staticmethod
    def update(db: Session, kb: KnowledgeBase, **kwargs) -> KnowledgeBase:
        for k, v in kwargs.items():
            setattr(kb, k, v)
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def soft_delete(db: Session, kb: KnowledgeBase) -> None:
        from datetime import datetime
        kb.deleted_at = datetime.utcnow()
        db.commit()
