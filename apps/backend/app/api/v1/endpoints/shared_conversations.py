from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.conversation import (
    ConversationShareRequest,
    ConversationShareResponse,
    SharedConversationResponse
)
from app.services.conversation_service import ConversationService

router = APIRouter(
    tags=["Conversation Public Sharing"]
)


@router.post(
    "/conversations/{id}/share",
    response_model=ConversationShareResponse,
    status_code=status.HTTP_200_OK
)
def share_conversation(
    id: int,
    request: ConversationShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a read-only public sharing link for a conversation.
    Supports expiry options: never, 24h, 7d, 30d.
    """
    return ConversationService.share_conversation(
        db=db,
        user_id=current_user.id,
        conversation_id=id,
        expires_in=request.expires_in
    )


@router.get(
    "/shared/{token}",
    response_model=SharedConversationResponse,
    status_code=status.HTTP_200_OK
)
def get_shared_conversation(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Public read-only endpoint to access a shared conversation using its token.
    Does not require authentication.
    """
    return ConversationService.get_shared_conversation(db, token)
