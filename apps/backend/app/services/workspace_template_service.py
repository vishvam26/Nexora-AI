import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.models.workspace_template import WorkspaceTemplate
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.folder import Folder
from app.models.conversation import Conversation
from app.repositories.workspace_template_repository import WorkspaceTemplateRepository
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.workspace_template_service")


class WorkspaceTemplateService:
    """
    Enterprise Template Service managing standard configurations, templated layouts, and quick workspace clone setups.
    """

    @staticmethod
    def create_template(
        db: Session,
        user_id: int,
        title: str,
        description: Optional[str],
        category: str,
        thumbnail: Optional[str],
        configuration: Dict[str, Any],
        is_public: bool = True
    ) -> WorkspaceTemplate:
        """
        Creates a reusable template configuration mapping folder and conversation skeletons.
        """
        template = WorkspaceTemplate(
            title=title,
            description=description,
            category=category,
            thumbnail=thumbnail,
            configuration=configuration,
            is_public=is_public,
            owner_id=user_id
        )
        return WorkspaceTemplateRepository.create(db, template)

    @staticmethod
    def list_templates(db: Session, user_id: int) -> List[WorkspaceTemplate]:
        """
        Lists public templates and user's private templates.
        """
        return WorkspaceTemplateRepository.list_public_and_owned(db, user_id)

    @staticmethod
    def delete_template(db: Session, user_id: int, template_id: int) -> None:
        """
        Deletes a template configuration. Only the owner can delete.
        """
        template = WorkspaceTemplateRepository.get_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        if template.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner of this template."
            )

        WorkspaceTemplateRepository.delete(db, template)

    @staticmethod
    def create_workspace_from_template(
        db: Session,
        user_id: int,
        template_id: int,
        workspace_name: str
    ) -> Workspace:
        """
        Spawns a new workspace initialized with folders and chats outlined in the template configuration.
        """
        template = WorkspaceTemplateRepository.get_by_id(db, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # 1. Create Workspace
        workspace = Workspace(
            owner_id=user_id,
            name=workspace_name,
            description=template.description or f"Created from template {template.title}"
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)

        # 2. Auto-provision OWNER membership
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user_id,
            role="OWNER",
            is_active=True
        )
        db.add(member)
        db.commit()

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace.id,
            user_id=user_id,
            action="Workspace Created",
            entity="Workspace",
            entity_id=workspace.id,
            metadata={"template_id": template_id}
        )

        # 3. Provision folders and conversations
        config = template.configuration or {}
        for folder_cfg in config.get("folders", []):
            folder_name = folder_cfg.get("name")
            if folder_name:
                folder = Folder(workspace_id=workspace.id, name=folder_name)
                db.add(folder)
                db.commit()
                db.refresh(folder)

                # Log activity
                ActivityService.log_activity(
                    db=db,
                    workspace_id=workspace.id,
                    user_id=user_id,
                    action="Folder Created",
                    entity="Folder",
                    entity_id=folder.id
                )

                for chat_title in folder_cfg.get("conversations", []):
                    convo = Conversation(
                        workspace_id=workspace.id,
                        user_id=user_id,
                        folder_id=folder.id,
                        title=chat_title
                    )
                    db.add(convo)
                    db.commit()
                    db.refresh(convo)

                    ActivityService.log_activity(
                        db=db,
                        workspace_id=workspace.id,
                        user_id=user_id,
                        action="Conversation Added",
                        entity="Conversation",
                        entity_id=convo.id
                    )

        return workspace
