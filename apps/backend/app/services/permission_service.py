from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember


class PermissionService:
    """
    Central permission engine managing Role-Based Access Control (RBAC) across workspaces.
    """

    @staticmethod
    def get_member_role(db: Session, user_id: int, workspace_id: int) -> str:
        """
        Gets a user's role in a workspace, falling back to OWNER if they own the workspace
        to ensure complete backward compatibility.
        """
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()

        if member:
            return member.role.upper()

        if workspace.owner_id == user_id:
            # Auto-provision OWNER workspace membership for complete backward compatibility
            new_member = WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                role="OWNER",
                is_active=True
            )
            db.add(new_member)
            db.commit()
            db.refresh(new_member)
            return "OWNER"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    @staticmethod
    def check_permission(
        db: Session,
        user_id: int,
        workspace_id: int,
        action: str,
        conversation_owner_id: Optional[int] = None
    ) -> None:
        """
        Enforces Role-Based Access Control policies.
        Raises HTTP 403 Forbidden on permission violation.
        """
        role = PermissionService.get_member_role(db, user_id, workspace_id)

        # OWNER can perform all actions
        if role == "OWNER":
            return

        # ADMIN permissions
        if role == "ADMIN":
            forbidden_admin_actions = ["transfer_ownership"]
            if action in forbidden_admin_actions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the workspace owner can perform this action"
                )
            return

        # EDITOR permissions
        if role == "EDITOR":
            allowed_editor_actions = [
                "create_conversation",
                "edit_conversation",
                "delete_conversation",
                "view_conversation",
                "move_conversation",
                "archive_conversation",
                "pin_conversation",
                "create_folder",
                "edit_folder",
                "delete_folder",
                "view_folder",
                "search",
                "view_workspace"
            ]
            if action not in allowed_editor_actions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace editors do not have permission for this action"
                )
            
            # Editors can only mutate/delete/move/archive conversations they created
            if action in ["edit_conversation", "delete_conversation", "move_conversation", "archive_conversation", "pin_conversation"]:
                if conversation_owner_id is not None and conversation_owner_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Editors can only modify their own conversations"
                    )
            return

        # VIEWER permissions
        if role == "VIEWER":
            allowed_viewer_actions = [
                "view_conversation",
                "view_folder",
                "view_workspace",
                "search"
            ]
            if action not in allowed_viewer_actions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace viewers have read-only access"
                )
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this action"
        )
