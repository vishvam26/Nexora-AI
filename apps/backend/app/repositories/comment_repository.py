from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.conversation_comment import ConversationComment


class CommentRepository:
    """
    Repository for handling database actions for ConversationComments.
    """

    @staticmethod
    def create(db: Session, comment: ConversationComment) -> ConversationComment:
        """
        Saves a new comment.
        """
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def get_by_id(db: Session, comment_id: int) -> Optional[ConversationComment]:
        """
        Retrieves comment by ID (if not soft deleted).
        """
        return db.query(ConversationComment).filter(
            ConversationComment.id == comment_id,
            ConversationComment.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_by_conversation(db: Session, conversation_id: int) -> List[ConversationComment]:
        """
        Retrieves all active top-level comments inside a conversation.
        Nested replies will load automatically via relationships.
        """
        return db.query(ConversationComment).filter(
            ConversationComment.conversation_id == conversation_id,
            ConversationComment.parent_comment_id.is_(None),
            ConversationComment.deleted_at.is_(None)
        ).order_by(ConversationComment.created_at.asc()).all()

    @staticmethod
    def update(db: Session, comment: ConversationComment, content: str) -> ConversationComment:
        """
        Updates comment contents.
        """
        comment.content = content
        comment.edited_at = datetime.utcnow()
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def soft_delete(db: Session, comment: ConversationComment) -> ConversationComment:
        """
        Soft deletes comment thread by setting deleted_at.
        """
        comment.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(comment)
        return comment
