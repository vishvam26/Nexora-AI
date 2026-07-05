import logging
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any, Optional, Dict
from app.models.folder import Folder
from app.repositories.folder_repository import FolderRepository
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService
from app.schemas.folder import FolderCreate, FolderUpdate

logger = logging.getLogger("app.services.folder_service")


class FolderService:
    """
    Service layer coordinating business validation, duplicate checking,
    ownership checks, and audit logging for Folders.
    """

    @staticmethod
    def create_folder(db: Session, user_id: int, schema: FolderCreate) -> Folder:
        """
        Validates workspace permission, checks duplicate name inside workspace,
        creates the Folder, logs activity and event.
        """
        # Validate workspace permission
        PermissionService.check_permission(db, user_id, schema.workspace_id, "create_folder")

        # Prevent duplicate folder names inside same workspace
        existing = FolderRepository.get_by_workspace_and_name(db, schema.workspace_id, schema.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder with this name already exists in this workspace"
            )

        folder = Folder(
            workspace_id=schema.workspace_id,
            name=schema.name,
            color=schema.color,
            icon=schema.icon
        )
        created_folder = FolderRepository.create(db, folder)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=schema.workspace_id,
            user_id=user_id,
            action="Folder Created",
            entity="Folder",
            entity_id=created_folder.id,
            metadata={"name": created_folder.name}
        )

        logger.info(
            "Folder created: owner_id=%s, workspace_id=%s, folder_id=%s, name='%s', timestamp=%s",
            user_id,
            schema.workspace_id,
            created_folder.id,
            created_folder.name,
            datetime.utcnow()
        )
        return created_folder

    @staticmethod
    def list_folders(db: Session, user_id: int, workspace_id: int) -> List[Folder]:
        """
        Lists all active folders inside a workspace, validating permission.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "view_folder")
        return FolderRepository.get_all_by_workspace_id(db, workspace_id)

    @staticmethod
    def get_folder_with_ownership(db: Session, user_id: int, folder_id: int) -> Folder:
        """
        Retrieves a folder, validating that its workspace is owned by the user.
        """
        folder = FolderRepository.get_by_id(db, folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
        # Validate workspace permission
        PermissionService.check_permission(db, user_id, folder.workspace_id, "view_folder")
        return folder

    @staticmethod
    def update_folder(db: Session, user_id: int, folder_id: int, schema: FolderUpdate) -> Folder:
        """
        Validates permission, checks name duplicates if updated, performs update and logs activity.
        """
        folder = FolderService.get_folder_with_ownership(db, user_id, folder_id)
        
        # Enforce edit permission
        PermissionService.check_permission(db, user_id, folder.workspace_id, "edit_folder")

        update_data = schema.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"] != folder.name:
            existing = FolderRepository.get_by_workspace_and_name(db, folder.workspace_id, update_data["name"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Folder with this name already exists in this workspace"
                )

        updated_folder = FolderRepository.update(db, folder, **update_data)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=folder.workspace_id,
            user_id=user_id,
            action="Folder Renamed",
            entity="Folder",
            entity_id=folder_id,
            metadata=update_data
        )

        logger.info(
            "Folder updated/renamed: owner_id=%s, folder_id=%s, timestamp=%s",
            user_id,
            updated_folder.id,
            datetime.utcnow()
        )
        return updated_folder

    @staticmethod
    def delete_folder(db: Session, user_id: int, folder_id: int) -> Folder:
        """
        Validates permission, soft deletes the folder, and logs activity.
        """
        folder = FolderService.get_folder_with_ownership(db, user_id, folder_id)
        
        # Enforce delete permission
        PermissionService.check_permission(db, user_id, folder.workspace_id, "delete_folder")

        deleted_folder = FolderRepository.soft_delete(db, folder)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=folder.workspace_id,
            user_id=user_id,
            action="Folder Deleted",
            entity="Folder",
            entity_id=folder_id,
            metadata={"name": folder.name}
        )

        logger.info(
            "Folder deleted: owner_id=%s, folder_id=%s, timestamp=%s",
            user_id,
            deleted_folder.id,
            datetime.utcnow()
        )
        return deleted_folder

    @staticmethod
    def restore_folder(db: Session, user_id: int, folder_id: int) -> Folder:
        """
        Restores a soft-deleted folder.
        """
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        PermissionService.check_permission(db, user_id, folder.workspace_id, "edit_folder")
        folder.deleted_at = None
        db.commit()
        db.refresh(folder)
        ActivityService.log_activity(db, folder.workspace_id, user_id, "Folder Restored", "Folder", folder_id)
        return folder

    @staticmethod
    def purge_folder(db: Session, user_id: int, folder_id: int) -> None:
        """
        Hard-deletes a folder permanently.
        """
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        PermissionService.check_permission(db, user_id, folder.workspace_id, "delete_folder")
        db.delete(folder)
        db.commit()
        ActivityService.log_activity(db, folder.workspace_id, user_id, "Folder Purged", "Folder", folder_id)

