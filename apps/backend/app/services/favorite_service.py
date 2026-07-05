import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.models.favorite import Favorite
from app.models.conversation import Conversation
from app.repositories.favorite_repository import FavoriteRepository
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.favorite_service")


class FavoriteService:
    """
    Service layer coordinating starred conversations and log auditing.
    """

    @staticmethod
    def add_favorite(db: Session, user_id: int, conversation_id: int) -> Favorite:
        """
        Favorites/Stars a conversation after verifying read permission and checking duplicate constraints.
        Logs auditable event.
        """
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.is_deleted == False
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Enforce read permission
        PermissionService.check_permission(db, user_id, conversation.workspace_id, "view_conversation")

        # Check unique constraint
        existing = FavoriteRepository.get_by_user_and_conversation(db, user_id, conversation_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation is already starred"
            )

        favorite = Favorite(
            user_id=user_id,
            conversation_id=conversation_id
        )
        created_favorite = FavoriteRepository.create(db, favorite)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action="Favorite Added",
            entity="Conversation",
            entity_id=conversation_id
        )

        return created_favorite

    @staticmethod
    def remove_favorite(db: Session, user_id: int, conversation_id: int) -> None:
        """
        Removes a conversation star/favorite.
        """
        favorite = FavoriteRepository.get_by_user_and_conversation(db, user_id, conversation_id)
        if not favorite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation is not starred"
            )

        FavoriteRepository.delete(db, favorite)

    @staticmethod
    def list_favorites(db: Session, user_id: int) -> List[Favorite]:
        """
        Returns all favorites saved by the user.
        """
        return FavoriteRepository.get_all_by_user(db, user_id)
