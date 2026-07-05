import logging
import re
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from app.models.conversation_comment import ConversationComment
from app.models.mention import Mention
from app.models.user import User
from app.models.workspace_member import WorkspaceMember
from app.repositories.comment_repository import CommentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.mention_repository import MentionRepository
from app.services.permission_service import PermissionService
from app.services.notification_service import NotificationService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.comment_service")


class CommentService:
    """
    Service layer coordinating comments CRUD, threaded replies,
    regex username mention scans, notifications, and auditable logging.
    """

    @staticmethod
    def create_comment(
        db: Session,
        user_id: int,
        conversation_id: int,
        content: str,
        parent_comment_id: Optional[int] = None
    ) -> ConversationComment:
        """
        Creates a comment inside a conversation. Enforces editor+ workspace permissions.
        Scans for @username mentions, creates Mention logs, and triggers alerts.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        workspace_id = conversation.workspace_id

        # Enforce editor+ permission to write comments
        PermissionService.check_permission(db, user_id, workspace_id, "edit_conversation")

        # Validate parent comment if provided
        if parent_comment_id is not None:
            parent = CommentRepository.get_by_id(db, parent_comment_id)
            if not parent or parent.conversation_id != conversation_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid parent comment thread"
                )

        comment = ConversationComment(
            conversation_id=conversation_id,
            user_id=user_id,
            parent_comment_id=parent_comment_id,
            content=content
        )
        created_comment = CommentRepository.create(db, comment)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Comment Added",
            entity="ConversationComment",
            entity_id=created_comment.id,
            metadata={"conversation_id": conversation_id}
        )

        # Scrape mentions (@name)
        # Find matches e.g. @JohnDoe
        tokens = re.findall(r"@([a-zA-Z0-9_]+)", content)
        actor = db.query(User).filter(User.id == user_id).first()

        # Retrieve active workspace members user records
        members = db.query(User).join(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).all()

        notified_users = set()

        for token in tokens:
            token_lower = token.lower()
            matched_user = None
            for u in members:
                normalized_fullname = u.full_name.replace(" ", "").lower()
                normalized_email = u.email.split("@")[0].lower()
                if normalized_fullname == token_lower or normalized_email == token_lower:
                    matched_user = u
                    break

            if matched_user and matched_user.id != user_id:
                # Save Mention record
                mention = Mention(
                    comment_id=created_comment.id,
                    mentioned_user_id=matched_user.id
                )
                MentionRepository.create(db, mention)
                notified_users.add(matched_user.id)

                # Log activity
                ActivityService.log_activity(
                    db=db,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    action="Mention Created",
                    entity="User",
                    entity_id=matched_user.id,
                    metadata={"comment_id": created_comment.id}
                )

                # Send Notification
                NotificationService.create_notification(
                    db=db,
                    user_id=matched_user.id,
                    workspace_id=workspace_id,
                    type_="MENTION",
                    title="Teammate Mentioned You",
                    message=f"{actor.full_name} mentioned you in a chat: '{content[:50]}...'",
                    entity_type="Conversation",
                    entity_id=conversation_id
                )

        # Notify Conversation Owner if it wasn't the caller, and owner wasn't already notified via @mention
        if conversation.user_id != user_id and conversation.user_id not in notified_users:
            NotificationService.create_notification(
                db=db,
                user_id=conversation.user_id,
                workspace_id=workspace_id,
                type_="COMMENT",
                title="New Comment on Chat",
                message=f"{actor.full_name} commented on your conversation.",
                entity_type="Conversation",
                entity_id=conversation_id
            )

        return created_comment

    @staticmethod
    def list_comments(db: Session, user_id: int, conversation_id: int) -> List[ConversationComment]:
        """
        Lists all comments inside a conversation. Enforces view permissions.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        PermissionService.check_permission(db, user_id, conversation.workspace_id, "view_conversation")
        return CommentRepository.get_by_conversation(db, conversation_id)

    @staticmethod
    def update_comment(db: Session, user_id: int, comment_id: int, content: str) -> ConversationComment:
        """
        Updates content of a comment, validating ownership.
        """
        comment = CommentRepository.get_by_id(db, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments"
            )

        updated_comment = CommentRepository.update(db, comment, content)

        # Log Activity
        conversation = ConversationRepository.get_by_id(db, comment.conversation_id)
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action="Comment Edited",
            entity="ConversationComment",
            entity_id=comment_id
        )

        return updated_comment

    @staticmethod
    def delete_comment(db: Session, user_id: int, comment_id: int) -> None:
        """
        Soft deletes comment. Allows deletes by comment owner or workspace admin/owner.
        """
        comment = CommentRepository.get_by_id(db, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )

        conversation = ConversationRepository.get_by_id(db, comment.conversation_id)
        role = PermissionService.get_member_role(db, user_id, conversation.workspace_id)

        # Validate deletion rights (Owner of comment, or workspace owner/admin)
        if comment.user_id != user_id and role not in ["OWNER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this comment"
            )

        CommentRepository.soft_delete(db, comment)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action="Comment Deleted",
            entity="ConversationComment",
            entity_id=comment_id
        )
