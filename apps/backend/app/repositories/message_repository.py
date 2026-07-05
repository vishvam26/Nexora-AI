from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.message import Message


class MessageRepository:
    """
    Repository for handling CRUD operations on the Message model.
    """

    @staticmethod
    def create(db: Session, message: Message) -> Message:
        """
        Saves a new Message to the database.
        """
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_by_id(db: Session, message_id: int) -> Optional[Message]:
        """
        Retrieves an active, non-deleted message by its ID.
        """
        return db.query(Message).filter(
            Message.id == message_id,
            Message.is_deleted == False
        ).first()

    @staticmethod
    def get_all_by_conversation_id(db: Session, conversation_id: int) -> List[Message]:
        """
        Retrieves all active, non-deleted messages belonging to a conversation,
        sorted by creation date in ascending order.
        """
        return db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).order_by(Message.created_at.asc()).all()

    @staticmethod
    def soft_delete(db: Session, message: Message) -> Message:
        """
        Flags a message as deleted (soft delete).
        """
        message.is_deleted = True
        db.commit()
        db.refresh(message)
        return message
