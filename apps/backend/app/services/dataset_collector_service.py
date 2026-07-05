import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger("app.services.dataset_collector_service")


class DatasetCollectorService:
    """
    Module 2: Conversation Collector
    Queries and aggregates chat logs based on project filter configurations.
    """

    @staticmethod
    def collect_conversations(
        db: Session,
        workspace_id: int,
        folder_id: int = None,
        only_good_chats: bool = False
    ) -> List[Conversation]:
        """
        Gathers list of conversation models matching workspace/folder guidelines.
        """
        query = db.query(Conversation).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.deleted_at.is_(None)
        )

        if folder_id:
            query = query.filter(Conversation.folder_id == folder_id)

        # Filtering based on summaries or feedback markers (future extension hook)
        if only_good_chats:
            pass

        return query.all()

    @staticmethod
    def get_messages_for_export(db: Session, conversation_ids: List[int]) -> List[Message]:
        """Gathers messages sorted by timestamp."""
        return (
            db.query(Message)
            .filter(Message.conversation_id.in_(conversation_ids))
            .order_by(Message.created_at.asc())
            .all()
        )
