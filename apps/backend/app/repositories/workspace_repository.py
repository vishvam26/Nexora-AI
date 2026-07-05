from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.workspace import Workspace


class WorkspaceRepository:
    """
    Repository for handling CRUD database operations on the Workspace model.
    Only raw SQL/ORM logic is performed here.
    """

    @staticmethod
    def create(db: Session, workspace: Workspace) -> Workspace:
        """
        Saves a new Workspace to the database.
        """
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        return workspace

    @staticmethod
    def get_by_id(db: Session, workspace_id: int) -> Optional[Workspace]:
        """
        Retrieves a specific workspace by ID if it has not been soft deleted.
        """
        return db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.deleted_at.is_(None)
        ).first()

    @staticmethod
    def get_all_by_owner_id(db: Session, owner_id: int) -> List[Workspace]:
        """
        Retrieves all active, non-deleted workspaces owned by a user.
        Sorted by creation time descending.
        """
        return db.query(Workspace).filter(
            Workspace.owner_id == owner_id,
            Workspace.deleted_at.is_(None)
        ).order_by(Workspace.created_at.desc()).all()

    @staticmethod
    def get_by_owner_and_name(db: Session, owner_id: int, name: str) -> Optional[Workspace]:
        """
        Retrieves an active workspace by owner ID and name.
        """
        return db.query(Workspace).filter(
            Workspace.owner_id == owner_id,
            Workspace.name == name,
            Workspace.deleted_at.is_(None)
        ).first()

    @staticmethod
    def soft_delete(db: Session, workspace: Workspace) -> Workspace:
        """
        Performs a soft delete by setting the deleted_at timestamp.
        """
        from datetime import datetime
        workspace.deleted_at = datetime.utcnow()
        workspace.status = "deleted"
        db.commit()
        db.refresh(workspace)
        return workspace

    @staticmethod
    def update(db: Session, workspace: Workspace, **kwargs) -> Workspace:
        """
        Updates specific workspace properties.
        """
        for key, value in kwargs.items():
            setattr(workspace, key, value)
        db.commit()
        db.refresh(workspace)
        return workspace
