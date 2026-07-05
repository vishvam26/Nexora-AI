from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.conversation import Conversation


class ConversationRepository:
    """
    Repository for handling CRUD operations on the Conversation model.
    """

    @staticmethod
    def create(db: Session, conversation: Conversation) -> Conversation:
        """
        Saves a new Conversation to the database.
        """
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_by_id(db: Session, conversation_id: int) -> Optional[Conversation]:
        """
        Retrieves a active, non-deleted conversation by its ID.
        """
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False
        ).first()

    @staticmethod
    def get_all_by_user_id(db: Session, user_id: int) -> List[Conversation]:
        """
        Retrieves all active, non-deleted conversations belonging to a user,
        sorted by creation date in descending order.
        """
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False
        ).order_by(Conversation.created_at.desc()).all()

    @staticmethod
    def get_conversations_filtered(
        db: Session,
        user_id: int,
        workspace_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        is_archived: bool = False,
        sort_by: str = "pinned_first",
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Retrieves active conversations with pagination, sorting, archiving, and folder filters.
        """
        query = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.is_archived == is_archived
        )

        if workspace_id is not None:
            query = query.filter(Conversation.workspace_id == workspace_id)

        if folder_id is not None:
            query = query.filter(Conversation.folder_id == folder_id)

        # Apply sorting
        if sort_by == "newest":
            query = query.order_by(Conversation.created_at.desc())
        elif sort_by == "oldest":
            query = query.order_by(Conversation.created_at.asc())
        elif sort_by == "alphabetical":
            query = query.order_by(Conversation.title.asc())
        elif sort_by == "recently_updated":
            query = query.order_by(Conversation.updated_at.desc())
        elif sort_by == "pinned_first":
            query = query.order_by(Conversation.is_pinned.desc(), Conversation.created_at.desc())
        else:
            query = query.order_by(Conversation.is_pinned.desc(), Conversation.created_at.desc())

        return query.offset(offset).limit(limit).all()


    @staticmethod
    def soft_delete(db: Session, conversation: Conversation) -> Conversation:
        """
        Flags a conversation as deleted (soft delete).
        """
        conversation.is_deleted = True
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def update(db: Session, conversation: Conversation, **kwargs) -> Conversation:
        """
        Updates fields of a Conversation and commits.
        """
        for key, value in kwargs.items():
            setattr(conversation, key, value)
        db.commit()
        db.refresh(conversation)
        return conversation

