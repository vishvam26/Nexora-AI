from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.workspace_invitation import (
    WorkspaceInvitationCreate,
    WorkspaceInvitationResponse,
    WorkspaceInvitationListResponse,
    AcceptInvitationRequest,
    DeclineInvitationRequest
)
from app.schemas.workspace_member import WorkspaceMemberResponse
from app.services.workspace_invitation_service import WorkspaceInvitationService

router = APIRouter(
    tags=["Workspace Invitations"]
)


@router.post(
    "/workspaces/{id}/invite",
    response_model=WorkspaceInvitationResponse,
    status_code=status.HTTP_201_CREATED
)
def invite_user(
    id: int,
    request: WorkspaceInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sends/Creates an invitation to join a workspace. Requires Manager privileges.
    """
    return WorkspaceInvitationService.create_invitation(
        db=db,
        user_id=current_user.id,
        workspace_id=id,
        email=request.email,
        role=request.role
    )


@router.get(
    "/workspaces/invitations",
    response_model=WorkspaceInvitationListResponse,
    status_code=status.HTTP_200_OK
)
def list_my_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns pending invitations matching the authenticated user's email address.
    """
    invitations = WorkspaceInvitationService.list_user_invitations(db, current_user.email)
    return WorkspaceInvitationListResponse(invitations=invitations)


@router.post(
    "/invitations/accept",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_200_OK
)
def accept_invitation(
    request: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts a pending invitation, adding the user to the workspace members.
    """
    return WorkspaceInvitationService.accept_invitation(
        db=db,
        user_id=current_user.id,
        email=current_user.email,
        token=request.token
    )


@router.post(
    "/invitations/decline",
    status_code=status.HTTP_200_OK
)
def decline_invitation(
    request: DeclineInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Declines a pending invitation, updating status to DECLINED.
    """
    WorkspaceInvitationService.decline_invitation(db, current_user.email, request.token)
    return {"status": "success", "detail": "Invitation successfully declined"}
