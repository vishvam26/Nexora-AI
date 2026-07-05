from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.message_reaction import MessageReaction


class ReactionRepository:
    """
    Repository for handling database actions for MessageReactions.
    """

    @staticmethod
    def create(db: Session, reaction: MessageReaction) -> MessageReaction:
        """
        Saves a new emoji reaction.
        """
        db.add(reaction)
        db.commit()
        db.refresh(reaction)
        return reaction

    @staticmethod
    def get_by_message_and_user_and_emoji(
        db: Session, message_id: int, user_id: int, emoji: str
    ) -> Optional[MessageReaction]:
        """
        Retrieves a user's exact reaction emoji on a message.
        """
        return db.query(MessageReaction).filter(
            MessageReaction.message_id == message_id,
            MessageReaction.user_id == user_id,
            MessageReaction.emoji == emoji
        ).first()

    @staticmethod
    def get_by_message(db: Session, message_id: int) -> List[MessageReaction]:
        """
        Retrieves all emoji reactions associated with a message.
        """
        return db.query(MessageReaction).filter(
            MessageReaction.message_id == message_id
        ).order_by(MessageReaction.created_at.asc()).all()

    @staticmethod
    def delete(db: Session, reaction: MessageReaction) -> None:
        """
        Removes reaction from database.
        """
        db.delete(reaction)
        db.commit()
