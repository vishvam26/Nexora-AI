from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.folder import FolderCreate, FolderUpdate, FolderResponse, FolderListResponse
from app.services.folder_service import FolderService

router = APIRouter(
    prefix="/folders",
    tags=["Folders"]
)


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_folder(
    request: FolderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new folder to organize conversations inside a workspace.
    """
    return FolderService.create_folder(db, current_user.id, request)


@router.get(
    "",
    response_model=FolderListResponse,
    status_code=status.HTTP_200_OK
)
def list_folders(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all active, non-deleted folders inside a workspace.
    """
    folders = FolderService.list_folders(db, current_user.id, workspace_id)
    return FolderListResponse(folders=folders)


@router.get(
    "/{id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK
)
def get_folder_details(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the details of a specific folder.
    """
    return FolderService.get_folder_with_ownership(db, current_user.id, id)


@router.patch(
    "/{id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK
)
def update_folder(
    id: int,
    request: FolderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates properties (name, color, icon) of a folder.
    """
    return FolderService.update_folder(db, current_user.id, id, request)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_folder(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft deletes a folder.
    """
    FolderService.delete_folder(db, current_user.id, id)
    return None


@router.post(
    "/{id}/restore",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK
)
def restore_folder(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores a soft-deleted folder back to active status.
    """
    return FolderService.restore_folder(db, current_user.id, id)


@router.delete(
    "/{id}/purge",
    status_code=status.HTTP_204_NO_CONTENT
)
def purge_folder(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a folder from the database.
    """
    FolderService.purge_folder(db, current_user.id, id)
    return None

