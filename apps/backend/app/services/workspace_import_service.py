import json
import logging
import zipfile
import io
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, UploadFile
from app.models.folder import Folder
from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.folder_repository import FolderRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.workspace_import_service")


class WorkspaceImportService:
    """
    Enterprise Import Engine parsing JSON, Markdown, ChatGPT/Claude backups, and ZIPs into active workspace structures.
    """

    @staticmethod
    def import_from_file(
        db: Session,
        user_id: int,
        workspace_id: int,
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        Parses uploaded file and imports conversations/folders into the specified workspace.
        """
        # Validate permissions
        PermissionService.check_permission(db, user_id, workspace_id, "edit_conversation")

        filename = file.filename or ""
        content_bytes = file.file.read()
        
        imported_stats = {
            "folders_created": 0,
            "conversations_created": 0,
            "messages_created": 0
        }

        try:
            if filename.endswith(".zip"):
                WorkspaceImportService._import_zip(db, user_id, workspace_id, content_bytes, imported_stats)
            elif filename.endswith(".json"):
                text_content = content_bytes.decode("utf-8", errors="ignore")
                json_data = json.loads(text_content)
                WorkspaceImportService._import_json(db, user_id, workspace_id, json_data, imported_stats)
            elif filename.endswith((".md", ".txt")):
                text_content = content_bytes.decode("utf-8", errors="ignore")
                WorkspaceImportService._import_markdown(db, user_id, workspace_id, text_content, imported_stats)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file format. Supported: .zip, .json, .md, .txt"
                )
        except Exception as e:
            db.rollback()
            logger.error(f"Import failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse import package: {str(e)}"
            )

        # Log import action
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Import Executed",
            entity="Workspace",
            entity_id=workspace_id,
            metadata=imported_stats
        )

        return {
            "status": "success",
            "imported": imported_stats
        }

    @staticmethod
    def _import_json(db: Session, user_id: int, workspace_id: int, data: Any, stats: Dict[str, int]) -> None:
        """
        Parses standard JSON schema, ChatGPT exports, or list of chats.
        """
        # 1. Standard format
        if isinstance(data, dict) and "folders" in data:
            for fold in data["folders"]:
                folder_model = Folder(workspace_id=workspace_id, name=fold["name"])
                db.add(folder_model)
                db.commit()
                db.refresh(folder_model)
                stats["folders_created"] += 1

                for convo in fold.get("conversations", []):
                    WorkspaceImportService._create_conversation_from_dict(
                        db, user_id, workspace_id, folder_model.id, convo, stats
                    )

            # Orphaned conversations
            for convo in data.get("conversations", []):
                WorkspaceImportService._create_conversation_from_dict(
                    db, user_id, workspace_id, None, convo, stats
                )

        # 2. List of chats format (ChatGPT/Claude/OpenAI compatible JSON array)
        elif isinstance(data, list):
            for item in data:
                # ChatGPT mapping style or simple dictionary
                if "title" in item and "mapping" in item:
                    # ChatGPT export parse
                    convo_title = item.get("title") or "Imported Chat"
                    convo = Conversation(workspace_id=workspace_id, user_id=user_id, title=convo_title)
                    db.add(convo)
                    db.commit()
                    db.refresh(convo)
                    stats["conversations_created"] += 1

                    for node in item["mapping"].values():
                        msg_node = node.get("message")
                        if msg_node and msg_node.get("content"):
                            role = msg_node["author"]["role"]
                            if role in ["user", "assistant"]:
                                parts = msg_node["content"].get("parts", [""])
                                text = "".join(parts)
                                if text:
                                    message = Message(
                                        conversation_id=convo.id,
                                        user_id=user_id,
                                        role=role,
                                        content=text
                                    )
                                    db.add(message)
                                    stats["messages_created"] += 1
                    db.commit()
                else:
                    # Simple chat dict
                    WorkspaceImportService._create_conversation_from_dict(
                        db, user_id, workspace_id, None, item, stats
                    )

    @staticmethod
    def _create_conversation_from_dict(
        db: Session,
        user_id: int,
        workspace_id: int,
        folder_id: Optional[int],
        convo_dict: Dict[str, Any],
        stats: Dict[str, int]
    ) -> None:
        title = convo_dict.get("title") or "Imported Chat"
        convo = Conversation(
            workspace_id=workspace_id,
            user_id=user_id,
            folder_id=folder_id,
            title=title
        )
        db.add(convo)
        db.commit()
        db.refresh(convo)
        stats["conversations_created"] += 1

        for msg in convo_dict.get("messages", []):
            role = msg.get("role") or "user"
            content = msg.get("content") or ""
            message = Message(
                conversation_id=convo.id,
                user_id=user_id,
                role=role,
                content=content
            )
            db.add(message)
            stats["messages_created"] += 1
        db.commit()

    @staticmethod
    def _import_markdown(db: Session, user_id: int, workspace_id: int, text: str, stats: Dict[str, int]) -> None:
        """
        Parses Markdown structured conversations.
        """
        lines = text.split("\n")
        current_convo = None
        current_role = None
        current_content = []

        def save_previous_message():
            nonlocal current_role, current_content
            if current_convo and current_role and current_content:
                msg = Message(
                    conversation_id=current_convo.id,
                    user_id=user_id,
                    role=current_role,
                    content="\n".join(current_content).strip()
                )
                db.add(msg)
                stats["messages_created"] += 1
                current_content = []

        for line in lines:
            line_strip = line.strip()
            # Detect conversation heading
            if line_strip.startswith("### Chat:") or line_strip.startswith("# "):
                save_previous_message()
                title = line_strip.split(":", 1)[-1].strip() if ":" in line_strip else line_strip.replace("#", "").strip()
                current_convo = Conversation(workspace_id=workspace_id, user_id=user_id, title=title)
                db.add(current_convo)
                db.commit()
                db.refresh(current_convo)
                stats["conversations_created"] += 1
                current_role = None
            elif line_strip.startswith(("**USER:**", "**user:**", "USER:")):
                save_previous_message()
                current_role = "user"
                current_content.append(line_strip.split(":", 1)[-1].strip())
            elif line_strip.startswith(("**ASSISTANT:**", "**assistant:**", "ASSISTANT:", "**SYSTEM:**")):
                save_previous_message()
                current_role = "assistant"
                current_content.append(line_strip.split(":", 1)[-1].strip())
            elif current_role:
                current_content.append(line)

        save_previous_message()
        db.commit()

    @staticmethod
    def _import_zip(db: Session, user_id: int, workspace_id: int, content_bytes: bytes, stats: Dict[str, int]) -> None:
        """
        Extracts ZIP backups looking for workspace_info.json or markdown compilations.
        """
        zip_io = io.BytesIO(content_bytes)
        with zipfile.ZipFile(zip_io, "r") as zip_file:
            # Look for workspace_info.json
            if "workspace_info.json" in zip_file.namelist():
                json_data = json.loads(zip_file.read("workspace_info.json").decode("utf-8"))
                WorkspaceImportService._import_json(db, user_id, workspace_id, json_data, stats)
            else:
                # Import all markdown files in the zip
                for name in zip_file.namelist():
                    if name.endswith((".md", ".txt")):
                        md_text = zip_file.read(name).decode("utf-8", errors="ignore")
                        WorkspaceImportService._import_markdown(db, user_id, workspace_id, md_text, stats)
