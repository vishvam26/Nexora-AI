from typing import List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.message import Message
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository


class MemoryService:
    """
    Service layer responsible for managing conversation history memory windows
    and prepending summaries to the AI prompt context.
    """

    @staticmethod
    def get_recent_history(
        db: Session, conversation_id: int, limit: Optional[int] = None
    ) -> List[Message]:
        """
        Loads the most recent N active messages for a conversation,
        sorted in chronological ascending order.
        """
        if limit is None:
            limit = settings.MAX_HISTORY_MESSAGES

        # Retrieve last N messages in descending order, then reverse
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).limit(limit).all()

        messages.reverse()
        return messages

    @staticmethod
    def update_memory(db: Session, conversation: Conversation) -> None:

        """
        Analyzes active message count, preparing logic for conversation summaries.
        Acts as a placeholder check for the SUMMARY_TRIGGER criteria.
        """
        # Count all active messages
        messages_count = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.is_deleted == False
        ).count()

        if messages_count >= settings.SUMMARY_TRIGGER:
            # Prepare architectural placeholder for summaries.
            # In the future, this can invoke an LLM call to summarize old messages,
            # save it in conversation.summary, and prune old database messages.
            # Currently stubs a placeholder summary to show execution integration.
            if not conversation.summary:
                placeholder_summary = (
                    f"Placeholder Summary (Messages threshold {settings.SUMMARY_TRIGGER} met). "
                    f"Active messages count: {messages_count}."
                )
                ConversationRepository.update(db, conversation, summary=placeholder_summary)
