from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.models.workspace_template import WorkspaceTemplate


class WorkspaceTemplateRepository:
    """
    Repository for handling database actions for WorkspaceTemplates.
    """

    @staticmethod
    def create(db: Session, template: WorkspaceTemplate) -> WorkspaceTemplate:
        """
        Saves a new workspace template.
        """
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_by_id(db: Session, template_id: int) -> Optional[WorkspaceTemplate]:
        """
        Retrieves template by ID.
        """
        return db.query(WorkspaceTemplate).filter(WorkspaceTemplate.id == template_id).first()

    @staticmethod
    def list_public_and_owned(db: Session, owner_id: int) -> List[WorkspaceTemplate]:
        """
        Retrieves all templates that are public or owned by the caller.
        """
        return db.query(WorkspaceTemplate).filter(
            or_(
                WorkspaceTemplate.is_public == True,
                WorkspaceTemplate.owner_id == owner_id
            )
        ).order_by(WorkspaceTemplate.created_at.desc()).all()

    @staticmethod
    def delete(db: Session, template: WorkspaceTemplate) -> None:
        """
        Permanently deletes a template.
        """
        db.delete(template)
        db.commit()
