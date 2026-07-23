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
        Gets a user's role in a workspace, falling back to MANAGER if they own the workspace
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
            return member.workspace_role.upper()

        if workspace.owner_id == user_id:
            # Auto-provision MANAGER workspace membership for complete backward compatibility
            new_member = WorkspaceMember(
                workspace_id=workspace_id,
                user_id=user_id,
                workspace_role="MANAGER",
                is_active=True
            )
            db.add(new_member)
            db.commit()
            db.refresh(new_member)
            return "MANAGER"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )

    @staticmethod
    def is_manager_of(db: Session, manager_id: int, employee_id: int) -> bool:
        """
        Recursively checks if manager_id is in the management chain above employee_id.
        """
        if not manager_id or not employee_id:
            return False
        if manager_id == employee_id:
            return True
        
        from app.models.user import User
        current = db.query(User).filter(User.id == employee_id).first()
        for _ in range(20):  # Safety recursion depth limit
            if not current or not current.manager_id:
                break
            if current.manager_id == manager_id:
                return True
            current = db.query(User).filter(User.id == current.manager_id).first()
            
        return False

    @staticmethod
    def validate_workspace_access(db: Session, user_id: int, workspace_id: int) -> None:
        """
        Enforces tenant company bounds and workspace access controls (including CEO/Manager hierarchy).
        Bypasses checks in standalone mode (workspace_id is None) or PERSONAL mode.
        """
        from app.config import settings
        if settings.APP_MODE == "PERSONAL" or workspace_id is None:
            return

        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        
        if not user or not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User or Workspace not found"
            )
            
        # 1. Company Tenant Isolation Check (Enterprise Mode Only)
        if settings.APP_MODE == "ENTERPRISE":
            if user.company_id != workspace.company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: tenant isolation mismatch"
                )
            
        # 2. CEO/Owner/Admin Check
        if user.company_role in ["OWNER", "ADMIN"]:
            return
            
        # 3. Workspace Membership Check
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True
        ).first()
        if member:
            return
            
        # 4. Management Hierarchy Check (Enterprise Mode Only)
        if settings.APP_MODE == "ENTERPRISE":
            if PermissionService.is_manager_of(db, user_id, workspace.owner_id):
                return
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this workspace"
        )

    @staticmethod
    def validate_conversation_access(db: Session, user_id: int, conversation_id: int) -> None:
        """
        Validates access to a conversation based on workspace permissions and management hierarchy.
        Supports standalone personal mode fallback.
        """
        from app.models.conversation import Conversation
        from app.models.user import User
        from app.config import settings
        
        user = db.query(User).filter(User.id == user_id).first()
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not user or not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User or Conversation not found"
            )
            
        # Standalone Mode Bypass: If conversation has no workspace associated or PERSONAL mode
        if settings.APP_MODE == "PERSONAL" or conv.workspace_id is None:
            if conv.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this standalone conversation"
                )
            return

        # Validate workspace access first
        PermissionService.validate_workspace_access(db, user_id, conv.workspace_id)
        
        # Non-admin/owner roles can only see own convs or of their subordinates (Enterprise Hierarchy only)
        if settings.APP_MODE == "ENTERPRISE" and user.company_role not in ["OWNER", "ADMIN"]:
            if conv.user_id != user_id and not PermissionService.is_manager_of(db, user_id, conv.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to access this conversation"
                )
        elif settings.APP_MODE == "TEAM":
            # Simple team workspace: can see own convs or admin can view all
            if conv.user_id != user_id:
                role = PermissionService.get_member_role(db, user_id, conv.workspace_id)
                if role not in ["OWNER", "ADMIN"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions to access this conversation"
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
        Enforces Role-Based Access Control policies for MANAGER and EMPLOYEE roles.
        Raises HTTP 403 Forbidden on permission violation.
        Supports standalone personal mode bypass.
        """
        from app.config import settings
        if settings.APP_MODE == "PERSONAL" or workspace_id is None:
            if conversation_owner_id is not None and conversation_owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to modify this standalone conversation"
                )
            return

        # Validate general workspace access first (tenant isolation, hierarchy, etc)
        PermissionService.validate_workspace_access(db, user_id, workspace_id)
        
        role = PermissionService.get_member_role(db, user_id, workspace_id)
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
 
        # MANAGER permissions
        if role == "MANAGER":
            if action == "transfer_ownership":
                if not workspace or workspace.owner_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Only the workspace owner can perform this action"
                    )
            return
 
        # EMPLOYEE permissions
        if role == "EMPLOYEE":
            allowed_employee_actions = [
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
            if action not in allowed_employee_actions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Workspace employees have limited access"
                )
            
            # Employees can only mutate/delete/move/archive conversations they created
            if action in ["edit_conversation", "delete_conversation", "move_conversation", "archive_conversation", "pin_conversation"]:
                if conversation_owner_id is not None and conversation_owner_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Employees can only modify their own conversations"
                    )
            return
 
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this action"
        )
