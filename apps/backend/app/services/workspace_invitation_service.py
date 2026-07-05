import logging
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.workspace_invitation import WorkspaceInvitation
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.repositories.workspace_invitation_repository import WorkspaceInvitationRepository
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.workspace_invitation_service")


class WorkspaceInvitationService:
    """
    Service layer coordinating invitation lifecycles, acceptances, and member additions.
    """

    @staticmethod
    def create_invitation(
        db: Session, user_id: int, workspace_id: int, email: str, role: str
    ) -> WorkspaceInvitation:
        """
        Validates caller is Owner/Admin, email is not already a member,
        generates UUID token, and creates a WorkspaceInvitation.
        """
        # Validate caller is Owner/Admin
        caller_role = PermissionService.get_member_role(db, user_id, workspace_id)
        if caller_role not in ["OWNER", "ADMIN"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners or admins can invite new members"
            )

        # Normalise email
        email = email.strip().lower()

        # Check if user is already a member
        # Find if a user account exists with this email
        invited_user = db.query(User).filter(User.email == email).first()
        if invited_user:
            existing_member = WorkspaceMemberRepository.get_by_workspace_and_user(db, workspace_id, invited_user.id)
            if existing_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a member of this workspace"
                )

        # Check if there is already an active pending invitation for this email
        existing_invite = WorkspaceInvitationRepository.get_pending_by_workspace_and_email(db, workspace_id, email)
        if existing_invite:
            # Check if expired
            if existing_invite.expires_at > datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An active invitation is already pending for this email in this workspace"
                )
            else:
                # Mark expired
                existing_invite.status = "EXPIRED"
                db.commit()

        # Create invitation
        expires_at = datetime.utcnow() + timedelta(days=7)
        invitation = WorkspaceInvitation(
            workspace_id=workspace_id,
            email=email,
            invited_by=user_id,
            role=role,
            token=str(uuid.uuid4()),
            status="PENDING",
            expires_at=expires_at
        )
        created_invite = WorkspaceInvitationRepository.create(db, invitation)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Member Invited",
            entity="WorkspaceInvitation",
            entity_id=created_invite.id,
            metadata={"invited_email": email, "role": role}
        )

        return created_invite

    @staticmethod
    def list_user_invitations(db: Session, email: str) -> List[WorkspaceInvitation]:
        """
        Lists pending invitations for a user email.
        Also automatically marks expired ones as EXPIRED.
        """
        email = email.strip().lower()
        invitations = WorkspaceInvitationRepository.get_pending_by_email(db, email)
        
        active_invites = []
        for invite in invitations:
            if invite.expires_at < datetime.utcnow():
                invite.status = "EXPIRED"
                db.commit()
            else:
                active_invites.append(invite)

        return active_invites

    @staticmethod
    def accept_invitation(db: Session, user_id: int, email: str, token: str) -> WorkspaceMember:
        """
        Validates token, accepts invitation, and adds the user to WorkspaceMembers.
        """
        invitation = WorkspaceInvitationRepository.get_by_token(db, token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        if invitation.status != "PENDING" or invitation.expires_at < datetime.utcnow():
            if invitation.status == "PENDING":
                invitation.status = "EXPIRED"
                db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired or is no longer pending"
            )

        if invitation.email.strip().lower() != email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation was sent to a different email address"
            )

        # Mark accepted
        WorkspaceInvitationRepository.update_status(db, invitation, "ACCEPTED")

        # Add to WorkspaceMembers
        # Check if already a member first
        existing_member = WorkspaceMemberRepository.get_by_workspace_and_user(db, invitation.workspace_id, user_id)
        if existing_member:
            return existing_member

        member = WorkspaceMember(
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role=invitation.role,
            is_active=True
        )
        created_member = WorkspaceMemberRepository.create(db, member)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            action="Member Joined",
            entity="User",
            entity_id=user_id,
            metadata={"role": invitation.role}
        )

        return created_member

    @staticmethod
    def decline_invitation(db: Session, email: str, token: str) -> None:
        """
        Declines a pending invitation.
        """
        invitation = WorkspaceInvitationRepository.get_by_token(db, token)
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        if invitation.status != "PENDING" or invitation.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has expired or is no longer pending"
            )

        if invitation.email.strip().lower() != email.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation belongs to a different email address"
            )

        WorkspaceInvitationRepository.update_status(db, invitation, "DECLINED")
