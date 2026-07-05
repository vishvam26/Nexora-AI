from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.workspace_template import (
    WorkspaceTemplateCreate,
    WorkspaceTemplateResponse,
    WorkspaceTemplateListResponse
)
from app.schemas.workspace import WorkspaceResponse
from app.services.workspace_template_service import WorkspaceTemplateService
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/templates",
    tags=["Workspace Templates"]
)


class TemplateCloneRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)


@router.post(
    "",
    response_model=WorkspaceTemplateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_workspace_template(
    request: WorkspaceTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new template setup configurations for workspaces cloning.
    """
    return WorkspaceTemplateService.create_template(
        db=db,
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        category=request.category,
        thumbnail=request.thumbnail,
        configuration=request.configuration,
        is_public=request.is_public
    )


@router.get(
    "",
    response_model=WorkspaceTemplateListResponse,
    status_code=status.HTTP_200_OK
)
def list_workspace_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns public templates and private ones owned by user.
    """
    templates = WorkspaceTemplateService.list_templates(db, current_user.id)
    return WorkspaceTemplateListResponse(templates=templates)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_workspace_template(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes template metadata permanently. Only template owner is allowed.
    """
    WorkspaceTemplateService.delete_template(db, current_user.id, id)
    return None


@router.post(
    "/{id}/clone",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED
)
def clone_workspace_from_template(
    id: int,
    request: TemplateCloneRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clones/Spawns a new workspace using structural configuration defined by the template.
    """
    return WorkspaceTemplateService.create_workspace_from_template(
        db=db,
        user_id=current_user.id,
        template_id=id,
        workspace_name=request.name
    )
