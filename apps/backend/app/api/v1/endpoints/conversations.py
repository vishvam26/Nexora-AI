from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    ConversationMove,
    ConversationStatsResponse
)
from app.schemas.conversation_version import ConversationVersionListResponse
from app.services.conversation_service import ConversationService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    schema: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation for the authenticated user.
    """
    return ConversationService.create_conversation(db, current_user.id, schema)


@router.get(
    "",
    response_model=ConversationListResponse
)
def get_conversations(
    workspace_id: Optional[int] = Query(None, description="Filter by Workspace ID"),
    folder_id: Optional[int] = Query(None, description="Filter by Folder ID"),
    is_archived: bool = Query(False, description="Filter by Archived status"),
    sort_by: str = Query("pinned_first", description="Sorting style: newest, oldest, alphabetical, recently_updated, pinned_first"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated and filtered conversations belonging to the authenticated user.
    """
    conversations = ConversationService.get_conversations(
        db=db,
        user_id=current_user.id,
        workspace_id=workspace_id,
        folder_id=folder_id,
        is_archived=is_archived,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )
    return ConversationListResponse(conversations=conversations)


@router.get(
    "/{id}",
    response_model=ConversationResponse
)
def get_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a single conversation by ID. Only the owner can access it.
    """
    return ConversationService.get_conversation_details(db, id, current_user.id)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft-delete a conversation by ID. Only the owner can delete it.
    """
    ConversationService.delete_conversation(db, id, current_user.id)
    return


@router.patch(
    "/{id}/move",
    response_model=ConversationResponse
)
def move_conversation(
    id: int,
    schema: ConversationMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Moves conversation to a target folder inside the workspace.
    """
    return ConversationService.move_conversation(db, current_user.id, id, schema.folder_id)


@router.patch(
    "/{id}/archive",
    response_model=ConversationResponse
)
def archive_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Archives a conversation.
    """
    return ConversationService.archive_conversation(db, current_user.id, id, archive=True)


@router.patch(
    "/{id}/restore",
    response_model=ConversationResponse
)
def restore_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores an archived conversation.
    """
    return ConversationService.archive_conversation(db, current_user.id, id, archive=False)


@router.patch(
    "/{id}/pin",
    response_model=ConversationResponse
)
def pin_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pins a conversation.
    """
    return ConversationService.pin_conversation(db, current_user.id, id, pin=True)


@router.patch(
    "/{id}/unpin",
    response_model=ConversationResponse
)
def unpin_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unpins a conversation.
    """
    return ConversationService.pin_conversation(db, current_user.id, id, pin=False)


@router.get(
    "/{id}/stats",
    response_model=ConversationStatsResponse
)
def get_conversation_stats(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compiles and returns stats metadata for a conversation.
    """
    return ConversationService.get_conversation_stats(db, current_user.id, id)


@router.post(
    "/{id}/restore-deleted",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK
)
def restore_deleted_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores a soft-deleted conversation back to active list.
    """
    return ConversationService.restore_conversation(db, current_user.id, id)


@router.delete(
    "/{id}/purge",
    status_code=status.HTTP_204_NO_CONTENT
)
def purge_conversation(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Hard-deletes a conversation permanently.
    """
    ConversationService.purge_conversation(db, current_user.id, id)
    return None


@router.get(
    "/{id}/versions",
    response_model=ConversationVersionListResponse,
    status_code=status.HTTP_200_OK
)
def list_conversation_versions(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves edit revision history list of message changes for a conversation.
    """
    versions = ConversationService.list_versions(db, current_user.id, id)
    return ConversationVersionListResponse(versions=versions)


@router.post(
    "/{id}/restore-version",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK
)
def restore_conversation_version(
    id: int,
    version_id: int = Query(..., description="ID of the revision snapshot version to restore to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reverts conversation message content to a previous edit version.
    """
    return ConversationService.restore_version(db, current_user.id, id, version_id)

