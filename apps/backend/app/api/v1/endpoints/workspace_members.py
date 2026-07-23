from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.workspace_member import (
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdate,
    WorkspaceOwnershipTransfer
)
from app.schemas.activity_log import ActivityLogListResponse
from app.services.workspace_member_service import WorkspaceMemberService
from app.services.activity_service import ActivityService

router = APIRouter(
    tags=["Workspace Members & Settings"]
)


@router.get(
    "/workspaces/{id}/members",
    response_model=List[WorkspaceMemberResponse],
    status_code=status.HTTP_200_OK
)
def list_workspace_members(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all active team members inside a workspace.
    """
    return WorkspaceMemberService.list_members(db, current_user.id, id)


@router.patch(
    "/workspaces/member/{id}/role",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_200_OK
)
def update_member_role(
    id: int,
    request: WorkspaceMemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Changes role (MANAGER, EMPLOYEE) of an existing workspace member.
    """
    return WorkspaceMemberService.update_member_role(db, current_user.id, id, request.workspace_role)


@router.delete(
    "/workspaces/member/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remove_workspace_member(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Removes a member from a workspace. Owner cannot remove self, Admin cannot remove Admin.
    """
    WorkspaceMemberService.remove_member(db, current_user.id, id)
    return None


@router.post(
    "/workspaces/{id}/transfer",
    status_code=status.HTTP_200_OK
)
def transfer_workspace_ownership(
    id: int,
    request: WorkspaceOwnershipTransfer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transfers ownership of a workspace to a target Admin. Old owner becomes Admin.
    """
    WorkspaceMemberService.transfer_ownership(db, current_user.id, id, request.target_user_id)
    return {"status": "success", "detail": f"Ownership successfully transferred to user {request.target_user_id}"}


@router.get(
    "/workspaces/{id}/activity",
    response_model=ActivityLogListResponse,
    status_code=status.HTTP_200_OK
)
def list_workspace_activity_logs(
    id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns auditable logs of workspace events (creation, invitations, archiving, sharing, etc).
    """
    logs = ActivityService.get_activity_logs(db, current_user.id, id, limit, offset)
    return ActivityLogListResponse(logs=logs)
