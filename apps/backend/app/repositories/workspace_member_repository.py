from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.workspace_member import WorkspaceMember


class WorkspaceMemberRepository:
    """
    Repository for handling database operations on WorkspaceMembers.
    """

    @staticmethod
    def create(db: Session, member: WorkspaceMember) -> WorkspaceMember:
        """
        Saves a new WorkspaceMember.
        """
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def get_by_workspace_and_user(db: Session, workspace_id: int, user_id: int) -> Optional[WorkspaceMember]:
        """
        Retrieves active membership by workspace ID and user ID.
        """
        return db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

    @staticmethod
    def get_all_by_workspace_id(db: Session, workspace_id: int) -> List[WorkspaceMember]:
        """
        Retrieves all active members in a workspace.
        """
        return db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).order_by(WorkspaceMember.joined_at.asc()).all()

    @staticmethod
    def get_by_id(db: Session, member_id: int) -> Optional[WorkspaceMember]:
        """
        Retrieves workspace member by record ID.
        """
        return db.query(WorkspaceMember).filter(
            WorkspaceMember.id == member_id,
            WorkspaceMember.is_active == True
        ).first()

    @staticmethod
    def update_role(db: Session, member: WorkspaceMember, role: str) -> WorkspaceMember:
        """
        Updates role field.
        """
        member.role = role
        db.commit()
        db.refresh(member)
        return member

    @staticmethod
    def remove(db: Session, member: WorkspaceMember) -> None:
        """
        Removes a member from the workspace (hard deletion).
        """
        db.delete(member)
        db.commit()
