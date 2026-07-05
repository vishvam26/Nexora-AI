from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.notification import Notification


class NotificationRepository:
    """
    Repository for handling database actions for Notifications.
    """

    @staticmethod
    def create(db: Session, notification: Notification) -> Notification:
        """
        Saves a new notification.
        """
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_unread_by_user(db: Session, user_id: int) -> List[Notification]:
        """
        Retrieves all unread notifications for a user, sorted by created_at descending.
        """
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_all_by_user(db: Session, user_id: int) -> List[Notification]:
        """
        Retrieves all notifications for a user, sorted by created_at descending.
        """
        return db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, notification_id: int) -> Optional[Notification]:
        """
        Retrieves a notification by ID.
        """
        return db.query(Notification).filter(Notification.id == notification_id).first()

    @staticmethod
    def mark_as_read(db: Session, notification: Notification) -> Notification:
        """
        Marks notification as read.
        """
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> None:
        """
        Marks all unread user notifications as read.
        """
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()

    @staticmethod
    def delete(db: Session, notification: Notification) -> None:
        """
        Permanently deletes a notification.
        """
        db.delete(notification)
        db.commit()
