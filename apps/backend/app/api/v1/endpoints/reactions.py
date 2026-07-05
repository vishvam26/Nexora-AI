from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.reaction import ReactionCreate, ReactionResponse, ReactionListResponse
from app.services.reaction_service import ReactionService

router = APIRouter(
    prefix="/messages",
    tags=["Message Reactions"]
)


@router.post(
    "/{id}/reaction",
    response_model=ReactionResponse,
    status_code=status.HTTP_201_CREATED
)
def add_message_reaction(
    id: int,
    request: ReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reacts to a message with an allowed emoji. Limit one reaction of this emoji type per user.
    """
    return ReactionService.add_reaction(db, current_user.id, id, request.emoji)


@router.delete(
    "/{id}/reaction",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_message_reaction(
    id: int,
    emoji: str = Query(..., description="The emoji reaction to remove"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes user's emoji reaction from a message.
    """
    ReactionService.remove_reaction(db, current_user.id, id, emoji)
    return None


@router.get(
    "/{id}/reactions",
    response_model=ReactionListResponse,
    status_code=status.HTTP_200_OK
)
def list_message_reactions(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all emoji reactions linked to a message.
    """
    reactions = ReactionService.list_reactions(db, current_user.id, id)
    return ReactionListResponse(reactions=reactions)
