import logging
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any, Optional, Dict
from app.models.workspace import Workspace
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.workspace_service")


class WorkspaceService:
    """
    Service layer containing business validations, duplicate checking,
    ownership security checks, and audit logging.
    """

    @staticmethod
    def create(db: Session, owner_id: int, schema: WorkspaceCreate) -> Workspace:
        """
        Validates duplicate names for the same owner, creates Workspace, provisions General folder,
        provisions OWNER membership, and logs activity.
        """
        # Reject duplicate workspace names for same owner
        existing = WorkspaceRepository.get_by_owner_and_name(db, owner_id, schema.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workspace with this name already exists for this owner"
            )

        workspace = Workspace(
            owner_id=owner_id,
            name=schema.name,
            description=schema.description,
            icon=schema.icon,
            color=schema.color,
            visibility=schema.visibility,
            status="active"
        )
        created_ws = WorkspaceRepository.create(db, workspace)

        # Auto-provision a default "General" folder inside the workspace
        from app.models.folder import Folder
        from app.repositories.folder_repository import FolderRepository
        general_folder = Folder(
            workspace_id=created_ws.id,
            name="General",
            color="Blue",
            icon="📁"
        )
        FolderRepository.create(db, general_folder)

        # Auto-provision OWNER workspace membership
        from app.models.workspace_member import WorkspaceMember
        from app.repositories.workspace_member_repository import WorkspaceMemberRepository
        owner_member = WorkspaceMember(
            workspace_id=created_ws.id,
            user_id=owner_id,
            role="OWNER",
            is_active=True
        )
        WorkspaceMemberRepository.create(db, owner_member)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=created_ws.id,
            user_id=owner_id,
            action="Workspace Created",
            entity="Workspace",
            entity_id=created_ws.id,
            metadata={"name": created_ws.name}
        )

        logger.info(
            "Workspace created: owner_id=%s, workspace_id=%s, name='%s', timestamp=%s",
            owner_id,
            created_ws.id,
            created_ws.name,
            datetime.utcnow()
        )
        return created_ws

    @staticmethod
    def list_for_user(db: Session, owner_id: int) -> List[Workspace]:
        """
        Returns all active workspaces where the user is an active member.
        Automatically provisions membership records for legacy owned workspaces for backward compatibility.
        """
        from app.models.workspace_member import WorkspaceMember

        # Fetch workspaces where this user is the registered owner
        owned_ws = db.query(Workspace).filter(
            Workspace.owner_id == owner_id,
            Workspace.deleted_at.is_(None)
        ).all()

        # Enforce that owners have a WorkspaceMember entry of role OWNER
        for ws in owned_ws:
            member = db.query(WorkspaceMember).filter(
                WorkspaceMember.workspace_id == ws.id,
                WorkspaceMember.user_id == owner_id,
                WorkspaceMember.is_active == True
            ).first()
            if not member:
                new_m = WorkspaceMember(
                    workspace_id=ws.id,
                    user_id=owner_id,
                    role="OWNER",
                    is_active=True
                )
                db.add(new_m)
                db.commit()

        # Query all active memberships for this user
        memberships = db.query(WorkspaceMember).filter(
            WorkspaceMember.user_id == owner_id,
            WorkspaceMember.is_active == True
        ).all()
        workspace_ids = [m.workspace_id for m in memberships]

        return db.query(Workspace).filter(
            Workspace.id.in_(workspace_ids),
            Workspace.deleted_at.is_(None)
        ).all()

    @staticmethod
    def get_workspace_with_ownership(db: Session, owner_id: int, workspace_id: int) -> Workspace:
        """
        Fetches a workspace and validates membership. Throws clear 404/403 errors.
        """
        # Ensure user has view access to this workspace
        PermissionService.check_permission(db, owner_id, workspace_id, "view_workspace")

        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        return workspace

    @staticmethod
    def update(db: Session, owner_id: int, workspace_id: int, schema: WorkspaceUpdate) -> Workspace:
        """
        Validates permission, checks duplicate names, updates fields, and logs action.
        """
        # Only ADMIN/OWNER can update workspace properties
        PermissionService.check_permission(db, owner_id, workspace_id, "transfer_ownership")

        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        update_data = schema.model_dump(exclude_unset=True)

        # Check duplicate name if renaming
        if "name" in update_data and update_data["name"] != workspace.name:
            existing = WorkspaceRepository.get_by_owner_and_name(db, owner_id, update_data["name"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Workspace with this name already exists for this owner"
                )

        updated_ws = WorkspaceRepository.update(db, workspace, **update_data)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=owner_id,
            action="Workspace Updated",
            entity="Workspace",
            entity_id=workspace_id,
            metadata=update_data
        )

        logger.info(
            "Workspace updated/renamed: owner_id=%s, workspace_id=%s, timestamp=%s",
            owner_id,
            updated_ws.id,
            datetime.utcnow()
        )
        return updated_ws

    @staticmethod
    def delete(db: Session, owner_id: int, workspace_id: int) -> Workspace:
        """
        Validates ownership, soft-deletes the workspace, and logs action.
        Only the OWNER can delete the workspace.
        """
        role = PermissionService.get_member_role(db, owner_id, workspace_id)
        if role != "OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the workspace owner can delete the workspace"
            )

        workspace = WorkspaceRepository.get_by_id(db, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        deleted_ws = WorkspaceRepository.soft_delete(db, workspace)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=owner_id,
            action="Workspace Deleted",
            entity="Workspace",
            entity_id=workspace_id
        )

        logger.info(
            "Workspace soft-deleted: owner_id=%s, workspace_id=%s, timestamp=%s",
            owner_id,
            deleted_ws.id,
            datetime.utcnow()
        )
        return deleted_ws

    @staticmethod
    def update_branding(db: Session, user_id: int, workspace_id: int, branding_data: dict) -> Workspace:
        """
        Updates logo, emoji, primary and accent colors for workspace branding.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "transfer_ownership")
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.deleted_at.is_(None)).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        for key, val in branding_data.items():
            setattr(workspace, key, val)
        db.commit()
        db.refresh(workspace)
        ActivityService.log_activity(db, workspace_id, user_id, "Branding Updated", "Workspace", workspace_id, branding_data)
        return workspace

    @staticmethod
    def update_settings(db: Session, user_id: int, workspace_id: int, settings_data: dict) -> Workspace:
        """
        Updates policies, timezone, language, and enterprise controls.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "transfer_ownership")
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.deleted_at.is_(None)).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        for key, val in settings_data.items():
            setattr(workspace, key, val)
        db.commit()
        db.refresh(workspace)
        ActivityService.log_activity(db, workspace_id, user_id, "Settings Updated", "Workspace", workspace_id, settings_data)
        return workspace

    @staticmethod
    def get_trash(db: Session, user_id: int, workspace_id: int) -> dict:
        """
        Returns soft-deleted conversations and folders.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")
        from app.models.folder import Folder
        from app.models.conversation import Conversation
        folders = db.query(Folder).filter(Folder.workspace_id == workspace_id, Folder.deleted_at.is_not(None)).all()
        conversations = db.query(Conversation).filter(Conversation.workspace_id == workspace_id, Conversation.is_deleted == True).all()
        return {"folders": folders, "conversations": conversations}

    @staticmethod
    def restore_workspace(db: Session, user_id: int, workspace_id: int) -> Workspace:
        """
        Restores a soft-deleted workspace. Only owner is allowed.
        """
        role = PermissionService.get_member_role(db, user_id, workspace_id)
        if role != "OWNER":
            raise HTTPException(status_code=403, detail="Only workspace owner can restore the workspace")
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        workspace.deleted_at = None
        workspace.status = "active"
        db.commit()
        db.refresh(workspace)
        ActivityService.log_activity(db, workspace_id, user_id, "Workspace Restored", "Workspace", workspace_id)
        return workspace

    @staticmethod
    def purge_workspace(db: Session, user_id: int, workspace_id: int) -> None:
        """
        Hard-deletes workspace permanently. Only owner is allowed.
        """
        role = PermissionService.get_member_role(db, user_id, workspace_id)
        if role != "OWNER":
            raise HTTPException(status_code=403, detail="Only workspace owner can purge the workspace")
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        db.delete(workspace)
        db.commit()
        ActivityService.log_activity(db, workspace_id, user_id, "Workspace Purged", "Workspace", workspace_id)

    @staticmethod
    def create_snapshot(db: Session, user_id: int, workspace_id: int) -> dict:
        """
        Compiles structural configuration overview of the workspace.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        from app.models.folder import Folder
        from app.models.conversation import Conversation
        folders = db.query(Folder.name).filter(Folder.workspace_id == workspace_id, Folder.deleted_at.is_(None)).all()
        conversations = db.query(Conversation.title).filter(Conversation.workspace_id == workspace_id, Conversation.is_deleted == False).all()
        snapshot_data = {
            "workspace_name": workspace.name,
            "folders": [f[0] for f in folders],
            "conversations": [c[0] for c in conversations],
            "timestamp": datetime.utcnow().isoformat()
        }
        ActivityService.log_activity(db, workspace_id, user_id, "Workspace Snapshot", "Workspace", workspace_id, snapshot_data)
        return snapshot_data

    @staticmethod
    def activity_replay(db: Session, user_id: int, workspace_id: int) -> List[Any]:
        """
        Returns chronological list of activities log in this workspace.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")
        from app.models.activity_log import ActivityLog
        return db.query(ActivityLog).filter(
            ActivityLog.workspace_id == workspace_id
        ).order_by(ActivityLog.created_at.asc()).all()

