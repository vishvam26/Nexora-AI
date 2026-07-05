from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Tuple, Optional
from app.models.conversation import Conversation
from app.models.message import Message


class SearchRepository:
    """
    Repository executing global search across titles, summaries, and message contents.
    """

    @staticmethod
    def global_search(
        db: Session,
        workspace_id: int,
        query: str,
        folder_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Tuple[Conversation, List[Message]]], int]:
        """
        Searches active conversations and matching messages using SQL ILIKE.
        Returns a list of tuples (Conversation, matched_messages_list) and total count.
        """
        # Base filter for active conversations
        convo_query = db.query(Conversation).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False
        )

        if folder_id is not None:
            convo_query = convo_query.filter(Conversation.folder_id == folder_id)

        # Keyword filter on Conversation Title / Summary or Message Content
        term = f"%{query}%"

        # We find all conversations matching title/summary
        # OR having messages matching term
        matching_conversations = convo_query.filter(
            or_(
                Conversation.title.ilike(term),
                Conversation.summary.ilike(term),
                Conversation.id.in_(
                    db.query(Message.conversation_id)
                    .filter(Message.content.ilike(term), Message.is_deleted == False)
                    .subquery()
                )
            )
        )

        total = matching_conversations.count()

        # Let's paginate and fetch conversations
        conversations = matching_conversations.order_by(
            Conversation.is_pinned.desc(),
            Conversation.created_at.desc()
        ).offset(offset).limit(limit).all()

        results = []
        for convo in conversations:
            # Retrieve matching messages inside this conversation
            matched_msgs = db.query(Message).filter(
                Message.conversation_id == convo.id,
                Message.content.ilike(term),
                Message.is_deleted == False
            ).order_by(Message.created_at.asc()).all()

            results.append((convo, matched_msgs))

        return results, total
