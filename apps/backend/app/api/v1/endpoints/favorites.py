from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.favorite import FavoriteResponse, FavoriteListResponse
from app.services.favorite_service import FavoriteService

router = APIRouter(
    tags=["Favorites"]
)


@router.post(
    "/conversations/{id}/favorite",
    response_model=FavoriteResponse,
    status_code=status.HTTP_201_CREATED
)
def add_favorite_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stars/favorites a conversation.
    """
    return FavoriteService.add_favorite(db, current_user.id, id)


@router.delete(
    "/conversations/{id}/favorite",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_favorite_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes star/favorite from a conversation.
    """
    FavoriteService.remove_favorite(db, current_user.id, id)
    return None


@router.get(
    "/favorites",
    response_model=FavoriteListResponse,
    status_code=status.HTTP_200_OK
)
def list_my_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all starred/favorited conversations of the authenticated user.
    """
    favorites = FavoriteService.list_favorites(db, current_user.id)
    return FavoriteListResponse(favorites=favorites)
