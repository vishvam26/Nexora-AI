from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.message import MessageCreate


class MessageService:
    """
    Service layer executing business validation and security checks for Messages.
    """

    @staticmethod
    def create_message(
        db: Session, user_id: int, schema: MessageCreate
    ) -> Message:
        """
        Creates a new message after verifying that the conversation exists
        and belongs to the authenticated user.
        """
        conversation = ConversationRepository.get_by_id(db, schema.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation"
            )

        message = Message(
            conversation_id=schema.conversation_id,
            role=schema.role,
            content=schema.content
        )
        return MessageRepository.create(db, message)

    @staticmethod
    def get_conversation_history(
        db: Session, conversation_id: int, user_id: int
    ) -> List[Message]:
        """
        Retrieves message history after verifying conversation ownership.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this conversation"
            )

        return MessageRepository.get_all_by_conversation_id(db, conversation_id)

    @staticmethod
    def delete_message(db: Session, message_id: int, user_id: int) -> None:
        """
        Soft-deletes a message after verifying that the containing conversation
        belongs to the authenticated user.
        """
        message = MessageRepository.get_by_id(db, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        conversation = ConversationRepository.get_by_id(db, message.conversation_id)
        if not conversation or conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this message"
            )

        MessageRepository.soft_delete(db, message)

    @staticmethod
    def update_message(
        db: Session, message_id: int, user_id: int, content: str, reason: Optional[str] = None
    ) -> Message:
        """
        Updates content of a message and saves a ConversationVersion snapshot history.
        """
        message = MessageRepository.get_by_id(db, message_id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        conversation = ConversationRepository.get_by_id(db, message.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Verify editing permission (owner of convo, or editor+ role in workspace)
        if conversation.user_id != user_id:
            from app.services.permission_service import PermissionService
            PermissionService.check_permission(db, user_id, conversation.workspace_id, "edit_conversation")

        if message.content != content:
            # Save ConversationVersion snapshot
            from app.models.conversation_version import ConversationVersion
            from app.repositories.conversation_version_repository import ConversationVersionRepository
            version = ConversationVersion(
                conversation_id=conversation.id,
                before_content=message.content,
                after_content=content,
                editor_id=user_id,
                reason=reason
            )
            ConversationVersionRepository.create(db, version)

            message.content = content
            db.commit()
            db.refresh(message)

            from app.services.activity_service import ActivityService
            ActivityService.log_activity(
                db=db,
                workspace_id=conversation.workspace_id,
                user_id=user_id,
                action="Message Edited",
                entity="Message",
                entity_id=message_id
            )

        return message

