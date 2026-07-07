import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import uuid
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.folder import Folder
from app.models.workspace import Workspace
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.folder_repository import FolderRepository
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService
from app.schemas.conversation import (
    ConversationCreate,
    ConversationStatsResponse,
    WorkspaceStatsResponse,
    ConversationShareResponse,
    SharedConversationResponse,
    SharedMessageResponse
)

logger = logging.getLogger("app.services.conversation_service")


class ConversationService:
    """
    Service layer executing business validation, RBAC checks, audit logging,
    and public link sharing lifecycles for Conversations.
    """

    @staticmethod
    def create_conversation(
        db: Session, user_id: int, schema: ConversationCreate
    ) -> Conversation:
        """
        Validates and creates a new conversation for a user inside a workspace and folder.
        Automatically provisions defaults if workspace or folder are missing.
        """
        # 1. Resolve workspace_id
        workspace_id = getattr(schema, "workspace_id", None)
        if workspace_id:
            workspace = db.query(Workspace).filter(
                Workspace.id == workspace_id,
                Workspace.deleted_at.is_(None)
            ).first()
            if not workspace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found"
                )
            # Enforce create_conversation permission
            PermissionService.check_permission(db, user_id, workspace_id, "create_conversation")
        else:
            # Locate default "Personal Workspace"
            default_ws = db.query(Workspace).filter(
                Workspace.owner_id == user_id,
                Workspace.deleted_at.is_(None)
            ).order_by(Workspace.id.asc()).first()

            if not default_ws:
                default_ws = Workspace(
                    owner_id=user_id,
                    name="Personal Workspace",
                    description="Your default personal workspace.",
                    icon="💼",
                    color="#4F46E5",
                    visibility="private",
                    status="active"
                )
                db.add(default_ws)
                db.commit()
                db.refresh(default_ws)

                # Provision default General folder inside the new default workspace
                general_folder = Folder(
                    workspace_id=default_ws.id,
                    name="General",
                    color="Blue",
                    icon="📁"
                )
                db.add(general_folder)
                db.commit()

                # Add membership for the owner
                from app.models.workspace_member import WorkspaceMember
                new_m = WorkspaceMember(
                    workspace_id=default_ws.id,
                    user_id=user_id,
                    role="OWNER",
                    is_active=True
                )
                db.add(new_m)
                db.commit()

            workspace_id = default_ws.id
            PermissionService.check_permission(db, user_id, workspace_id, "create_conversation")

        # 2. Resolve folder_id inside workspace
        folder_id = getattr(schema, "folder_id", None)
        if folder_id:
            folder = FolderRepository.get_by_id(db, folder_id)
            if not folder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Folder not found"
                )
            if folder.workspace_id != workspace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Folder does not belong to this workspace"
                )
        else:
            # Locate default "General" folder inside the workspace
            general_folder = db.query(Folder).filter(
                Folder.workspace_id == workspace_id,
                Folder.name == "General",
                Folder.deleted_at.is_(None)
            ).first()

            if not general_folder:
                general_folder = Folder(
                    workspace_id=workspace_id,
                    name="General",
                    color="Blue",
                    icon="📁"
                )
                db.add(general_folder)
                db.commit()
                db.refresh(general_folder)

            folder_id = general_folder.id

        conversation = Conversation(
            user_id=user_id,
            title=schema.title,
            workspace_id=workspace_id,
            folder_id=folder_id
        )
        created_convo = ConversationRepository.create(db, conversation)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Conversation Created",
            entity="Conversation",
            entity_id=created_convo.id,
            metadata={"title": created_convo.title}
        )

        return created_convo

    @staticmethod
    def get_conversations(
        db: Session,
        user_id: int,
        workspace_id: Optional[int] = None,
        folder_id: Optional[int] = None,
        is_archived: bool = False,
        sort_by: str = "pinned_first",
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """
        Retrieves paginated conversations, validating workspace read permissions.
        """
        # Validate workspace ownership/membership if supplied
        if workspace_id is not None:
            PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")
        else:
            # Find all workspaces the user has memberships in
            from app.models.workspace_member import WorkspaceMember
            memberships = db.query(WorkspaceMember).filter(
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_active == True
            ).all()
            # If no workspace specified, check permission on all of user's active workspaces
            # Under the hood, get_conversations_filtered will return only user's owned/accessible chats.
            pass

        # Validate folder membership if supplied
        if folder_id is not None:
            from app.services.folder_service import FolderService
            FolderService.get_folder_with_ownership(db, user_id, folder_id)

        return ConversationRepository.get_conversations_filtered(
            db, user_id, workspace_id, folder_id, is_archived, sort_by, limit, offset
        )

    @staticmethod
    def get_conversation_details(
        db: Session, conversation_id: int, user_id: int
    ) -> Conversation:
        """
        Retrieves conversation details, checking workspace read permission.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        # Ensure user can view conversations in this workspace
        PermissionService.check_permission(
            db=db,
            user_id=user_id,
            workspace_id=conversation.workspace_id,
            action="view_conversation"
        )
        return conversation

    @staticmethod
    def delete_conversation(
        db: Session, conversation_id: int, user_id: int
    ) -> None:
        """
        Soft deletes a conversation after asserting deletion rights.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Enforce delete permission (checking conversation user_id for Editor validation)
        PermissionService.check_permission(
            db=db,
            user_id=user_id,
            workspace_id=conversation.workspace_id,
            action="delete_conversation",
            conversation_owner_id=conversation.user_id
        )

        ConversationRepository.soft_delete(db, conversation)

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action="Conversation Deleted",
            entity="Conversation",
            entity_id=conversation_id,
            metadata={"title": conversation.title}
        )

    @staticmethod
    def move_conversation(
        db: Session, user_id: int, conversation_id: int, folder_id: Optional[int]
    ) -> Conversation:
        """
        Moves conversation to target folder inside same workspace after enforcing write permissions.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Enforce write permissions
        PermissionService.check_permission(
            db=db,
            user_id=user_id,
            workspace_id=conversation.workspace_id,
            action="move_conversation",
            conversation_owner_id=conversation.user_id
        )

        target_folder_id = folder_id
        if target_folder_id is None:
            # Retrieve default General folder of workspace
            general_folder = db.query(Folder).filter(
                Folder.workspace_id == conversation.workspace_id,
                Folder.name == "General",
                Folder.deleted_at.is_(None)
            ).first()
            if not general_folder:
                general_folder = Folder(
                    workspace_id=conversation.workspace_id,
                    name="General",
                    color="Blue",
                    icon="📁"
                )
                db.add(general_folder)
                db.commit()
                db.refresh(general_folder)
            target_folder_id = general_folder.id
        else:
            # Validate target folder ownership and matching workspace
            from app.services.folder_service import FolderService
            folder = FolderService.get_folder_with_ownership(db, user_id, target_folder_id)
            if folder.workspace_id != conversation.workspace_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Target folder belongs to a different workspace"
                )

        updated_convo = ConversationRepository.update(db, conversation, folder_id=target_folder_id)
        
        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action="Conversation Moved",
            entity="Conversation",
            entity_id=conversation_id,
            metadata={"target_folder_id": target_folder_id}
        )

        logger.info(
            "Conversation moved: owner_id=%s, conversation_id=%s, target_folder_id=%s, timestamp=%s",
            user_id,
            conversation_id,
            target_folder_id,
            datetime.utcnow()
        )
        return updated_convo

    @staticmethod
    def archive_conversation(
        db: Session, user_id: int, conversation_id: int, archive: bool
    ) -> Conversation:
        """
        Toggles is_archived status, checking write rights and logs activity.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        PermissionService.check_permission(
            db=db,
            user_id=user_id,
            workspace_id=conversation.workspace_id,
            action="archive_conversation",
            conversation_owner_id=conversation.user_id
        )

        updated_convo = ConversationRepository.update(db, conversation, is_archived=archive)
        
        # Log Activity
        action_name = "Conversation Archived" if archive else "Conversation Restored"
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action=action_name,
            entity="Conversation",
            entity_id=conversation_id
        )

        logger.info(
            "Conversation archive status changed: owner_id=%s, conversation_id=%s, is_archived=%s, timestamp=%s",
            user_id,
            conversation_id,
            archive,
            datetime.utcnow()
        )
        return updated_convo

    @staticmethod
    def pin_conversation(
        db: Session, user_id: int, conversation_id: int, pin: bool
    ) -> Conversation:
        """
        Toggles is_pinned status, checking write rights and logs activity.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        PermissionService.check_permission(
            db=db,
            user_id=user_id,
            workspace_id=conversation.workspace_id,
            action="pin_conversation",
            conversation_owner_id=conversation.user_id
        )

        updated_convo = ConversationRepository.update(db, conversation, is_pinned=pin)
        
        # Log Activity
        action_name = "Conversation Pinned" if pin else "Conversation Unpinned"
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action=action_name,
            entity="Conversation",
            entity_id=conversation_id
        )

        logger.info(
            "Conversation pin status changed: owner_id=%s, conversation_id=%s, is_pinned=%s, timestamp=%s",
            user_id,
            conversation_id,
            pin,
            datetime.utcnow()
        )
        return updated_convo

    @staticmethod
    def get_conversation_stats(
        db: Session, user_id: int, conversation_id: int
    ) -> ConversationStatsResponse:
        """
        Compiles stats metadata, checking read rights.
        """
        conversation = ConversationService.get_conversation_details(db, conversation_id, user_id)
        
        messages_count = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.is_deleted == False
        ).count()

        return ConversationStatsResponse(
            messages_count=messages_count,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_pinned=conversation.is_pinned,
            is_archived=conversation.is_archived
        )

    @staticmethod
    def get_workspace_stats(
        db: Session, user_id: int, workspace_id: int
    ) -> WorkspaceStatsResponse:
        """
        Compiles stats metadata, checking read rights.
        """
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")

        folders_count = db.query(Folder).filter(
            Folder.workspace_id == workspace_id,
            Folder.deleted_at.is_(None)
        ).count()

        conversations_count = db.query(Conversation).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False
        ).count()

        messages_count = db.query(Message).filter(
            Message.conversation_id.in_(
                db.query(Conversation.id).filter(
                    Conversation.workspace_id == workspace_id,
                    Conversation.is_deleted == False
                ).subquery()
            ),
            Message.is_deleted == False
        ).count()

        # Find last active message
        last_active_msg = db.query(Message).filter(
            Message.conversation_id.in_(
                db.query(Conversation.id).filter(
                    Conversation.workspace_id == workspace_id,
                    Conversation.is_deleted == False
                ).subquery()
            ),
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).first()

        last_active = last_active_msg.created_at if last_active_msg else None

        return WorkspaceStatsResponse(
            folders_count=folders_count,
            conversations_count=conversations_count,
            messages_count=messages_count,
            last_active=last_active
        )

    @staticmethod
    def share_conversation(
        db: Session, user_id: int, conversation_id: int, expires_in: str
    ) -> ConversationShareResponse:
        """
        Generates public UUID share token and expiry date, updates Conversation, logs activity and returns payload.
        """
        conversation = ConversationRepository.get_by_id(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Enforce view/share permission
        PermissionService.check_permission(
            db=db,
            user_id=user_id,
            workspace_id=conversation.workspace_id,
            action="view_conversation"
        )

        share_token = str(uuid.uuid4())
        
        # Calculate expiry
        expires_at = None
        if expires_in == "24h":
            expires_at = datetime.utcnow() + timedelta(hours=24)
        elif expires_in == "7d":
            expires_at = datetime.utcnow() + timedelta(days=7)
        elif expires_in == "30d":
            expires_at = datetime.utcnow() + timedelta(days=30)

        # Save updates
        ConversationRepository.update(
            db, conversation, share_token=share_token, share_expires_at=expires_at
        )

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=conversation.workspace_id,
            user_id=user_id,
            action="Workspace Shared",
            entity="Conversation",
            entity_id=conversation_id,
            metadata={"share_token": share_token, "expires_in": expires_in}
        )

        share_url = f"/shared/{share_token}"

        return ConversationShareResponse(
            share_token=share_token,
            share_url=share_url,
            expires_at=expires_at
        )

    @staticmethod
    def get_shared_conversation(db: Session, token: str) -> SharedConversationResponse:
        """
        Retrieves a public shared conversation by token if valid and not expired.
        Returns conversation title, summary, and complete history of messages.
        """
        conversation = db.query(Conversation).filter(
            Conversation.share_token == token,
            Conversation.is_deleted == False
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shared conversation not found or link has been deactivated"
            )

        # Check expiry
        if conversation.share_expires_at and conversation.share_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="This shared conversation link has expired"
            )

        # Retrieve messages chronologically
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.is_deleted == False
        ).order_by(Message.created_at.asc()).all()

        message_responses = [
            SharedMessageResponse.model_validate(msg) for msg in messages
        ]

        return SharedConversationResponse(
            id=conversation.id,
            title=conversation.title,
            summary=conversation.summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_responses
        )

    @staticmethod
    def restore_conversation(db: Session, user_id: int, conversation_id: int) -> Conversation:
        """
        Restores a soft-deleted conversation.
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        PermissionService.check_permission(db, user_id, conversation.workspace_id, "edit_conversation")
        conversation.is_deleted = False
        db.commit()
        db.refresh(conversation)
        ActivityService.log_activity(db, conversation.workspace_id, user_id, "Conversation Restored", "Conversation", conversation_id)
        return conversation

    @staticmethod
    def purge_conversation(db: Session, user_id: int, conversation_id: int) -> None:
        """
        Hard-deletes a conversation permanently.
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        PermissionService.check_permission(db, user_id, conversation.workspace_id, "delete_conversation")
        db.delete(conversation)
        db.commit()
        ActivityService.log_activity(db, conversation.workspace_id, user_id, "Conversation Purged", "Conversation", conversation_id)

    @staticmethod
    def list_versions(db: Session, user_id: int, conversation_id: int) -> List[Any]:
        """
        Retrieves all version snapshots for a conversation.
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        PermissionService.check_permission(db, user_id, conversation.workspace_id, "view_conversation")
        from app.repositories.conversation_version_repository import ConversationVersionRepository
        return ConversationVersionRepository.get_by_conversation(db, conversation_id)

    @staticmethod
    def restore_version(db: Session, user_id: int, conversation_id: int, version_id: int) -> Conversation:
        """
        Restores a conversation message version history step.
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        PermissionService.check_permission(db, user_id, conversation.workspace_id, "edit_conversation")

        from app.repositories.conversation_version_repository import ConversationVersionRepository
        version = ConversationVersionRepository.get_by_id(db, version_id)
        if not version or version.conversation_id != conversation_id:
            raise HTTPException(status_code=400, detail="Invalid version ID for this conversation")

        # Find the message whose content matches after_content and restore to before_content
        message = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.content == version.after_content,
            Message.is_deleted == False
        ).first()

        if message:
            message.content = version.before_content
            db.commit()

        # Log Activity
        ActivityService.log_activity(db, conversation.workspace_id, user_id, "Conversation Version Restored", "Conversation", conversation_id, {"version_id": version_id})
        return conversation

    @staticmethod
    def update_conversation(db: Session, user_id: int, conversation_id: int, schema: Any) -> Conversation:
        """
        Updates fields of an existing conversation.
        """
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.is_deleted == False).first()
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        PermissionService.check_permission(db, user_id, conversation.workspace_id, "edit_conversation")
        
        update_data = schema.dict(exclude_unset=True)
        updated = ConversationRepository.update(db, conversation, **update_data)
        
        ActivityService.log_activity(
            db,
            conversation.workspace_id,
            user_id,
            "Conversation Updated",
            "Conversation",
            conversation_id,
            update_data
        )
        return updated


