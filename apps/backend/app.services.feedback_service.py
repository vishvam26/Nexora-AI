import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.chat_feedback import ChatFeedback

logger = logging.getLogger("app.services.feedback_service")


class FeedbackService:
    """
    Module 3: User Feedback Learning
    Manages user thumbs-up/down ratings and logs feedback audits.
    """

    @staticmethod
    def submit_feedback(
        db: Session,
        user_id: int,
        conversation_id: int,
        message_id: int,
        rating: int = None,
        thumbs_up: bool = False,
        thumbs_down: bool = False,
        feedback: str = None
    ) -> ChatFeedback:
        """
        Creates and persists feedback log for a chat response.
        """
        record = ChatFeedback(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            thumbs_up=thumbs_up,
            thumbs_down=thumbs_down,
            feedback=feedback
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_feedback_analytics(db: Session, workspace_id: int) -> Dict[str, Any]:
        """
        Computes thumbs up/down totals.
        """
        # Using a direct SQL query to count feedback since workspace_id is linked through conversations
        from app.models.conversation import Conversation
        total_up = (
            db.query(ChatFeedback)
            .join(Conversation, ChatFeedback.conversation_id == Conversation.id)
            .filter(Conversation.workspace_id == workspace_id, ChatFeedback.thumbs_up == True)
            .count()
        )
        total_down = (
            db.query(ChatFeedback)
            .join(Conversation, ChatFeedback.conversation_id == Conversation.id)
            .filter(Conversation.workspace_id == workspace_id, ChatFeedback.thumbs_down == True)
            .count()
        )

        return {
            "thumbs_up": total_up,
            "thumbs_down": total_down,
            "total_reviews": total_up + total_down
        }
