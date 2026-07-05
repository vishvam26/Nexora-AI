import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.notification import Notification
from app.repositories.notification_repository import NotificationRepository
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.notification_service")


class NotificationService:
    """
    Service layer coordinating Workspace alerts, user reads/deletes, and audit logging.
    """

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        workspace_id: int,
        type_: str,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None
    ) -> Notification:
        """
        Creates and stores a notification alert.
        """
        notification = Notification(
            user_id=user_id,
            workspace_id=workspace_id,
            type=type_,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id
        )
        return NotificationRepository.create(db, notification)

    @staticmethod
    def list_notifications(
        db: Session, user_id: int, unread_only: bool = False
    ) -> List[Notification]:
        """
        Retrieves user notifications sorted chronologically descending.
        """
        if unread_only:
            return NotificationRepository.get_unread_by_user(db, user_id)
        return NotificationRepository.get_all_by_user(db, user_id)

    @staticmethod
    def mark_as_read(db: Session, user_id: int, notification_id: int) -> Notification:
        """
        Marks user notification as read, validating ownership.
        """
        notification = NotificationRepository.get_by_id(db, notification_id)
        if not notification:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="You do not own this notification")

        updated = NotificationRepository.mark_as_read(db, notification)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=notification.workspace_id,
            user_id=user_id,
            action="Notification Read",
            entity="Notification",
            entity_id=notification_id
        )

        return updated

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int, workspace_id: int) -> None:
        """
        Marks all unread user notifications as read in a given workspace context.
        """
        NotificationRepository.mark_all_as_read(db, user_id)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Notification Read All",
            entity="Workspace",
            entity_id=workspace_id
        )

    @staticmethod
    def delete_notification(db: Session, user_id: int, notification_id: int) -> None:
        """
        Deletes a user notification.
        """
        notification = NotificationRepository.get_by_id(db, notification_id)
        if not notification:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Notification not found")

        if notification.user_id != user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="You do not own this notification")

        NotificationRepository.delete(db, notification)
