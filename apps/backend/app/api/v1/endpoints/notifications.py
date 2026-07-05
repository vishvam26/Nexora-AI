from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK
)
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all notifications for the authenticated user.
    """
    notifications = NotificationService.list_notifications(db, current_user.id, unread_only=False)
    return NotificationListResponse(notifications=notifications)


@router.get(
    "/unread",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK
)
def list_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only unread notifications for the authenticated user.
    """
    notifications = NotificationService.list_notifications(db, current_user.id, unread_only=True)
    return NotificationListResponse(notifications=notifications)


@router.patch(
    "/{id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK
)
def mark_notification_read(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks a specific notification as read.
    """
    return NotificationService.mark_as_read(db, current_user.id, id)


@router.patch(
    "/read-all",
    status_code=status.HTTP_200_OK
)
def mark_all_notifications_read(
    workspace_id: int = Query(..., description="Workspace ID to target notifications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marks all unread notifications of the user as read.
    """
    NotificationService.mark_all_as_read(db, current_user.id, workspace_id)
    return {"status": "success", "detail": "All notifications marked as read"}


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a notification alert.
    """
    NotificationService.delete_notification(db, current_user.id, id)
    return None
