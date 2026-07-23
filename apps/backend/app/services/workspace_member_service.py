import logging
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.repositories.workspace_member_repository import WorkspaceMemberRepository
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.workspace_member_service")


class WorkspaceMemberService:
    """
    Service layer coordinating Workspace Membership, Roles, and Ownership transfers.
    """

    @staticmethod
    def list_members(db: Session, user_id: int, workspace_id: int) -> List[WorkspaceMember]:
        """
        Lists all active members in a workspace, verifying view membership first.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")
        return WorkspaceMemberRepository.get_all_by_workspace_id(db, workspace_id)

    @staticmethod
    def update_member_role(
        db: Session, user_id: int, member_id: int, new_role: str
    ) -> WorkspaceMember:
        """
        Updates workspace_role field of a member under strict RBAC restrictions.
        """
        target_member = WorkspaceMemberRepository.get_by_id(db, member_id)
        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member record not found"
            )

        workspace_id = target_member.workspace_id
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        acting_role = PermissionService.get_member_role(db, user_id, workspace_id)

        # Owner validations
        if workspace and workspace.owner_id == target_member.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify the role of the workspace owner. Ownership must be transferred instead."
            )

        # RBAC validations
        if acting_role == "EMPLOYEE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to modify member roles"
            )

        # If acting user is a MANAGER but NOT the owner:
        if acting_role == "MANAGER" and workspace and workspace.owner_id != user_id:
            if target_member.workspace_role == "MANAGER":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace managers can only be modified by the workspace owner"
                )
            if new_role == "MANAGER":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the workspace owner can promote members to MANAGER"
                )

        updated_member = WorkspaceMemberRepository.update_role(db, target_member, new_role)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Member Role Changed",
            entity="WorkspaceMember",
            entity_id=updated_member.id,
            metadata={"target_user_id": target_member.user_id, "new_role": new_role}
        )

        return updated_member

    @staticmethod
    def remove_member(db: Session, user_id: int, member_id: int) -> None:
        """
        Removes a member from the workspace under strict safety and role constraints.
        """
        target_member = WorkspaceMemberRepository.get_by_id(db, member_id)
        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member record not found"
            )

        workspace_id = target_member.workspace_id
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        acting_role = PermissionService.get_member_role(db, user_id, workspace_id)

        # Prevent owner deletion
        if workspace and workspace.owner_id == target_member.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the workspace owner"
            )

        # Prevent self removal via member edit
        if target_member.user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use workspace leave instead of deleting yourself"
            )

        if acting_role == "EMPLOYEE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to remove members"
            )

        if acting_role == "MANAGER" and workspace and workspace.owner_id != user_id:
            # Manager cannot delete other Managers
            if target_member.workspace_role == "MANAGER":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace managers can only be removed by the workspace owner"
                )

        WorkspaceMemberRepository.remove(db, target_member)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Member Removed",
            entity="User",
            entity_id=target_member.user_id,
            metadata={"removed_user_id": target_member.user_id}
        )

    @staticmethod
    def transfer_ownership(db: Session, user_id: int, workspace_id: int, target_user_id: int) -> Workspace:
        """
        Transfers workspace ownership. Target user must be an active workspace MANAGER.
        Owner remains MANAGER. Workspace owner_id is updated.
        """
        workspace = db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.deleted_at.is_(None)
        ).first()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Validate owner is acting
        if workspace.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the workspace owner can transfer ownership"
            )

        # Get target member record
        target_member = WorkspaceMemberRepository.get_by_workspace_and_user(db, workspace_id, target_user_id)
        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target user is not a member of this workspace"
            )

        if target_member.workspace_role != "MANAGER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ownership can only be transferred to an existing workspace MANAGER"
            )

        # Get current owner member record
        owner_member = WorkspaceMemberRepository.get_by_workspace_and_user(db, workspace_id, user_id)
        if not owner_member:
            # Auto-provision owner member if missing
            owner_member = WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                workspace_role="MANAGER",
                is_active=True
            )
            db.add(owner_member)
            db.commit()
            db.refresh(owner_member)

        # Confirm roles and swap owner_id
        target_member.workspace_role = "MANAGER"
        owner_member.workspace_role = "MANAGER"
        workspace.owner_id = target_user_id

        db.commit()

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Workspace Owner Transferred",
            entity="Workspace",
            entity_id=workspace_id,
            metadata={"new_owner_user_id": target_user_id, "old_owner_user_id": user_id}
        )

        return workspace
