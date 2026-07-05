from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse, CommentListResponse
from app.services.comment_service import CommentService

router = APIRouter(
    prefix="/comments",
    tags=["Comments"]
)


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    request: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new comment or nested threaded reply inside a conversation.
    Supports @username mention scraping.
    """
    return CommentService.create_comment(
        db=db,
        user_id=current_user.id,
        conversation_id=request.conversation_id,
        content=request.content,
        parent_comment_id=request.parent_comment_id
    )


@router.get(
    "/{conversation}",
    response_model=CommentListResponse,
    status_code=status.HTTP_200_OK
)
def list_conversation_comments(
    conversation: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves threaded comments and nested replies inside a conversation.
    """
    comments = CommentService.list_comments(db, current_user.id, conversation)
    return CommentListResponse(comments=comments)


@router.patch(
    "/{id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK
)
def update_comment(
    id: int,
    request: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Edits the text content of a comment. Only the comment creator can edit.
    """
    return CommentService.update_comment(db, current_user.id, id, request.content)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft-deletes a comment. Only comment owner or workspace admins/owners can delete.
    """
    CommentService.delete_comment(db, current_user.id, id)
    return None
