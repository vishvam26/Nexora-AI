from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.conversation_version import ConversationVersion


class ConversationVersionRepository:
    """
    Repository for handling database actions for ConversationVersions.
    """

    @staticmethod
    def create(db: Session, version: ConversationVersion) -> ConversationVersion:
        """
        Saves a new message revision snapshot.
        """
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def get_by_conversation(db: Session, conversation_id: int) -> List[ConversationVersion]:
        """
        Retrieves all revision histories for a specific conversation.
        """
        return db.query(ConversationVersion).filter(
            ConversationVersion.conversation_id == conversation_id
        ).order_by(ConversationVersion.created_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, version_id: int) -> Optional[ConversationVersion]:
        """
        Retrieves a specific revision record.
        """
        return db.query(ConversationVersion).filter(ConversationVersion.id == version_id).first()
