import logging
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.models.message_reaction import MessageReaction
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.user import User
from app.repositories.reaction_repository import ReactionRepository
from app.services.permission_service import PermissionService
from app.services.notification_service import NotificationService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.reaction_service")


class ReactionService:
    """
    Service layer coordinating individual message emoji reactions, alerts, and logging.
    """

    @staticmethod
    def add_reaction(db: Session, user_id: int, message_id: int, emoji: str) -> MessageReaction:
        """
        Reacts to a message. Enforces editor+ permission, validates unique emoji reaction per user-message,
        triggers notification alert, and logs activity.
        """
        # Fetch message and conversation context
        message = db.query(Message).filter(Message.id == message_id, Message.is_deleted == False).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        conversation = db.query(Conversation).filter(
            Conversation.id == message.conversation_id,
            Conversation.is_deleted == False
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation context not found"
            )

        workspace_id = conversation.workspace_id

        # Enforce write permissions (editor+)
        PermissionService.check_permission(db, user_id, workspace_id, "edit_conversation")

        # Check unique constraint
        existing = ReactionRepository.get_by_message_and_user_and_emoji(db, message_id, user_id, emoji)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reacted with this emoji to this message"
            )

        reaction = MessageReaction(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji
        )
        created_reaction = ReactionRepository.create(db, reaction)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Reaction Added",
            entity="MessageReaction",
            entity_id=created_reaction.id,
            metadata={"message_id": message_id, "emoji": emoji}
        )

        # Send Notification alert to the message owner (usually assistant or another user)
        # Verify message owner is a user account, not AI assistant role
        if message.role == "user" and conversation.user_id != user_id:
            actor = db.query(User).filter(User.id == user_id).first()
            NotificationService.create_notification(
                db=db,
                user_id=conversation.user_id,
                workspace_id=workspace_id,
                type_="REACTION",
                title="Message Reacted",
                message=f"{actor.full_name} reacted with {emoji} to your message.",
                entity_type="Conversation",
                entity_id=conversation.id
            )

        return created_reaction

    @staticmethod
    def remove_reaction(db: Session, user_id: int, message_id: int, emoji: str) -> None:
        """
        Removes an emoji reaction from a message.
        """
        reaction = ReactionRepository.get_by_message_and_user_and_emoji(db, message_id, user_id, emoji)
        if not reaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reaction not found"
            )

        ReactionRepository.delete(db, reaction)

    @staticmethod
    def list_reactions(db: Session, user_id: int, message_id: int) -> List[MessageReaction]:
        """
        Lists all reactions associated with a message.
        """
        # Fetch message and check read permission
        message = db.query(Message).filter(Message.id == message_id, Message.is_deleted == False).first()
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        conversation = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()
        if conversation:
            PermissionService.check_permission(db, user_id, conversation.workspace_id, "view_conversation")

        return ReactionRepository.get_by_message(db, message_id)
