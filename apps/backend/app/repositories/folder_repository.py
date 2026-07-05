from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.folder import Folder


class FolderRepository:
    """
    Repository for executing CRUD database operations on Folders.
    Filters out soft-deleted records.
    """

    @staticmethod
    def create(db: Session, folder: Folder) -> Folder:
        """
        Saves a new Folder to the database.
        """
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def get_by_id(db: Session, folder_id: int) -> Optional[Folder]:
        """
        Retrieves an active, non-deleted folder by its ID.
        """
        return db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_all_by_workspace_id(db: Session, workspace_id: int) -> List[Folder]:
        """
        Retrieves all active, non-deleted folders inside a workspace.
        """
        return db.query(Folder).filter(
            Folder.workspace_id == workspace_id,
            Folder.deleted_at.is_(None)
        ).order_by(Folder.created_at.asc()).all()

    @staticmethod
    def get_by_workspace_and_name(db: Session, workspace_id: int, name: str) -> Optional[Folder]:
        """
        Retrieves an active folder inside a workspace matching a given name.
        Used to prevent duplicate folder names.
        """
        return db.query(Folder).filter(
            Folder.workspace_id == workspace_id,
            Folder.name == name,
            Folder.deleted_at.is_(None)
        ).first()

    @staticmethod
    def soft_delete(db: Session, folder: Folder) -> Folder:
        """
        Soft deletes a folder by setting the deleted_at timestamp.
        """
        from datetime import datetime
        folder.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(folder)
        return folder

    @staticmethod
    def update(db: Session, folder: Folder, **kwargs) -> Folder:
        """
        Updates specific properties of a Folder.
        """
        for key, value in kwargs.items():
            setattr(folder, key, value)
        db.commit()
        db.refresh(folder)
        return folder
