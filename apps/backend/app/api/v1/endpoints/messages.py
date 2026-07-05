from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    MessageUpdate,
)
from app.services.message_service import MessageService

router = APIRouter(
    prefix="/messages",
    tags=["Messages"]
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_message(
    schema: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new message in a conversation.
    The authenticated user must own the target conversation.
    """
    return MessageService.create_message(db, current_user.id, schema)


@router.get(
    "/{conversation_id}",
    response_model=MessageListResponse
)
def get_conversation_history(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active messages in a conversation.
    The authenticated user must own the target conversation.
    """
    messages = MessageService.get_conversation_history(db, conversation_id, current_user.id)
    return MessageListResponse(messages=messages)


@router.patch(
    "/{id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK
)
def update_message(
    id: int,
    request: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the content of an existing message.
    Automatically logs a version revision snapshot.
    """
    return MessageService.update_message(db, id, current_user.id, request.content, request.reason)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_message(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft-delete a message by ID.
    Only the owner of the containing conversation can delete a message.
    """
    MessageService.delete_message(db, id, current_user.id)
    return

