from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.conversation import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get(
    "",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK
)
def global_search(
    workspace_id: int = Query(..., description="The ID of the workspace to search in"),
    query: str = Query(..., min_length=1, description="Keyword search query"),
    folder_id: Optional[int] = Query(None, description="Optional folder ID to filter search results"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Performs global keyword search across titles, summaries, and message contents.
    Requires workspace ownership.
    """
    return SearchService.search(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        query=query,
        folder_id=folder_id,
        limit=limit,
        offset=offset
    )
