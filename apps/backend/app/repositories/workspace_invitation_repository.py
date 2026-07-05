from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.workspace_invitation import WorkspaceInvitation


class WorkspaceInvitationRepository:
    """
    Repository for handling database operations on WorkspaceInvitations.
    """

    @staticmethod
    def create(db: Session, invitation: WorkspaceInvitation) -> WorkspaceInvitation:
        """
        Saves a new WorkspaceInvitation.
        """
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def get_by_token(db: Session, token: str) -> Optional[WorkspaceInvitation]:
        """
        Retrieves invitation matching token.
        """
        return db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.token == token
        ).first()

    @staticmethod
    def get_pending_by_email(db: Session, email: str) -> List[WorkspaceInvitation]:
        """
        Retrieves all pending invitations sent to an email.
        """
        return db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.email == email,
            WorkspaceInvitation.status == "PENDING"
        ).order_by(WorkspaceInvitation.created_at.desc()).all()

    @staticmethod
    def get_pending_by_workspace_and_email(db: Session, workspace_id: int, email: str) -> Optional[WorkspaceInvitation]:
        """
        Checks if there is an active pending invitation for this workspace & email.
        """
        return db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == email,
            WorkspaceInvitation.status == "PENDING"
        ).first()

    @staticmethod
    def update_status(db: Session, invitation: WorkspaceInvitation, status: str) -> WorkspaceInvitation:
        """
        Updates invitation status.
        """
        from datetime import datetime
        invitation.status = status
        if status == "ACCEPTED":
            invitation.accepted_at = datetime.utcnow()
        db.commit()
        db.refresh(invitation)
        return invitation
