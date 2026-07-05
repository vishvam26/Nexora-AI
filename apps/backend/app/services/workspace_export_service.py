import json
import logging
import io
import zipfile
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.workspace import Workspace
from app.models.folder import Folder
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.conversation_comment import ConversationComment
from app.models.message_reaction import MessageReaction
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.workspace_export_service")


class WorkspaceExportService:
    """
    Enterprise Export Engine aggregating workspace assets and rendering to JSON, Markdown, HTML, or ZIP archives.
    """

    @staticmethod
    def aggregate_data(
        db: Session,
        user_id: int,
        workspace_id: int,
        folder_id: Optional[int] = None,
        conversation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compiles all messages, comments, reactions, members, and metadata in a structured dict.
        Enforces view permissions.
        """
        # Validate permissions
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")

        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # Check enterprise policy
        if workspace.disable_exports:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Exports are disabled by enterprise policies in this workspace."
            )

        # Retrieve members
        members_query = db.query(User.id, User.full_name, User.email).join(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).all()
        participants = [{"id": m[0], "name": m[1], "email": m[2]} for m in members_query]

        # Retrieve Folders
        folders = []
        if conversation_id:
            # Single conversation scope
            convo = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.workspace_id == workspace_id,
                Conversation.is_deleted == False
            ).first()
            if not convo:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversations_to_export = [convo]
        elif folder_id:
            # Single folder scope
            folder = db.query(Folder).filter(
                Folder.id == folder_id,
                Folder.workspace_id == workspace_id,
                Folder.deleted_at.is_(None)
            ).first()
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            folders = [folder]
            conversations_to_export = db.query(Conversation).filter(
                Conversation.folder_id == folder_id,
                Conversation.is_deleted == False
            ).all()
        else:
            # Entire workspace scope
            folders = db.query(Folder).filter(
                Folder.workspace_id == workspace_id,
                Folder.deleted_at.is_(None)
            ).all()
            conversations_to_export = db.query(Conversation).filter(
                Conversation.workspace_id == workspace_id,
                Conversation.is_deleted == False
            ).all()

        folder_map = {f.id: {"id": f.id, "name": f.name, "conversations": []} for f in folders}
        orphaned_conversations = []

        # Load all messages, comments, and reactions
        for convo in conversations_to_export:
            messages = db.query(Message).filter(
                Message.conversation_id == convo.id,
                Message.is_deleted == False
            ).order_by(Message.created_at.asc()).all()

            comments = db.query(ConversationComment).filter(
                ConversationComment.conversation_id == convo.id,
                ConversationComment.deleted_at.is_(None)
            ).order_by(ConversationComment.created_at.asc()).all()

            convo_data = {
                "id": convo.id,
                "title": convo.title,
                "created_at": convo.created_at.isoformat(),
                "is_pinned": convo.is_pinned,
                "is_archived": convo.is_archived,
                "messages": [],
                "comments": []
            }

            # Map comments
            for c in comments:
                convo_data["comments"].append({
                    "id": c.id,
                    "user_id": c.user_id,
                    "parent_comment_id": c.parent_comment_id,
                    "content": c.content,
                    "created_at": c.created_at.isoformat()
                })

            # Map messages and reactions
            for msg in messages:
                reactions = db.query(MessageReaction.emoji, User.full_name).join(User).filter(
                    MessageReaction.message_id == msg.id
                ).all()
                rx_data = [{"emoji": r[0], "user_name": r[1]} for r in reactions]

                convo_data["messages"].append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "reactions": rx_data
                })

            if convo.folder_id in folder_map:
                folder_map[convo.folder_id]["conversations"].append(convo_data)
            else:
                orphaned_conversations.append(convo_data)

        # Log export event
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Export Generated",
            entity="Workspace",
            entity_id=workspace_id,
            metadata={"folder_id": folder_id, "conversation_id": conversation_id}
        )

        return {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "exported_at": datetime.utcnow().isoformat(),
            "participants": participants,
            "folders": list(folder_map.values()),
            "conversations": orphaned_conversations
        }

    @staticmethod
    def render_markdown(data: Dict[str, Any]) -> str:
        """
        Renders consolidated workspace data into an elegant markdown script.
        """
        md = []
        md.append(f"# Workspace Export: {data['workspace_name']}")
        md.append(f"Exported at: {data['exported_at']}\n")

        md.append("## Participants")
        for p in data["participants"]:
            md.append(f"- {p['name']} ({p['email']})")
        md.append("\n")

        # Process folders
        for folder in data["folders"]:
            md.append(f"## Folder: {folder['name']}")
            for convo in folder["conversations"]:
                md.append(f"### Chat: {convo['title']}")
                md.append(f"*Created at: {convo['created_at']}*\n")
                md.append("#### Messages")
                for msg in convo["messages"]:
                    md.append(f"**{msg['role'].upper()}:** {msg['content']}")
                    if msg["reactions"]:
                        rxs = ", ".join([f"{r['emoji']} ({r['user_name']})" for r in msg["reactions"]])
                        md.append(f"  *Reactions: {rxs}*")
                    md.append("")
                md.append("#### Thread Comments")
                for c in convo["comments"]:
                    md.append(f"- {c['content']} *(User: {c['user_id']} at {c['created_at']})*")
                md.append("\n" + "---" + "\n")

        # Process orphaned conversations
        if data["conversations"]:
            md.append("## Conversations")
            for convo in data["conversations"]:
                md.append(f"### Chat: {convo['title']}")
                md.append(f"*Created at: {convo['created_at']}*\n")
                md.append("#### Messages")
                for msg in convo["messages"]:
                    md.append(f"**{msg['role'].upper()}:** {msg['content']}")
                    if msg["reactions"]:
                        rxs = ", ".join([f"{r['emoji']} ({r['user_name']})" for r in msg["reactions"]])
                        md.append(f"  *Reactions: {rxs}*")
                    md.append("")
                md.append("#### Thread Comments")
                for c in convo["comments"]:
                    md.append(f"- {c['content']} *(User: {c['user_id']} at {c['created_at']})*")
                md.append("\n" + "---" + "\n")

        return "\n".join(md)

    @staticmethod
    def render_html(data: Dict[str, Any]) -> str:
        """
        Renders workspace export data into fully responsive beautiful HTML chats.
        """
        html = []
        html.append("<!DOCTYPE html><html><head><meta charset='utf-8'><title>Workspace Export</title>")
        html.append("<style>")
        html.append("body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f3f4f6; color: #111827; margin: 0; padding: 20px; }")
        html.append(".container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }")
        html.append(".chat-bubble { padding: 12px 16px; border-radius: 16px; margin-bottom: 12px; max-width: 80%; display: inline-block; clear: both; }")
        html.append(".user-bubble { background: #4f46e5; color: white; float: right; }")
        html.append(".assistant-bubble { background: #e5e7eb; color: #1f2937; float: left; }")
        html.append(".chat-title { font-weight: bold; margin-top: 30px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }")
        html.append("</style></head><body><div class='container'>")
        html.append(f"<h1>Workspace: {data['workspace_name']}</h1>")
        html.append(f"<p>Export Date: {data['exported_at']}</p>")

        for folder in data["folders"]:
            html.append(f"<h2>Folder: {folder['name']}</h2>")
            for convo in folder["conversations"]:
                html.append(f"<div class='chat-title'>Chat: {convo['title']}</div>")
                html.append("<div style='margin: 20px 0;'>")
                for msg in convo["messages"]:
                    bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
                    html.append(f"<div class='chat-bubble {bubble_class}'>")
                    html.append(f"<strong>{msg['role']}:</strong> {msg['content']}")
                    html.append("</div><div style='clear: both;'></div>")
                html.append("</div>")

        html.append("</div></body></html>")
        return "".join(html)

    @staticmethod
    def render_zip(data: Dict[str, Any]) -> io.BytesIO:
        """
        Packs the exported workspace structure into a neat download ZIP file.
        """
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Save workspace raw json metadata
            zip_file.writestr("workspace_info.json", json.dumps(data, indent=2))

            # 2. Save complete markdown compilation
            md_content = WorkspaceExportService.render_markdown(data)
            zip_file.writestr("full_export.md", md_content)

            # 3. Save elegant HTML preview
            html_content = WorkspaceExportService.render_html(data)
            zip_file.writestr("full_export.html", html_content)

            # 4. Save individual folder and conversation markdown files
            for folder in data["folders"]:
                folder_name = folder["name"].replace("/", "_").replace("\\", "_")
                for convo in folder["conversations"]:
                    convo_title = convo["title"].replace("/", "_").replace("\\", "_")
                    single_convo_md = []
                    single_convo_md.append(f"# {convo['title']}")
                    single_convo_md.append(f"Created: {convo['created_at']}\n")
                    for msg in convo["messages"]:
                        single_convo_md.append(f"**{msg['role'].upper()}:** {msg['content']}\n")

                    zip_file.writestr(f"folders/{folder_name}/{convo_title}.md", "\n".join(single_convo_md))

        zip_buffer.seek(0)
        return zip_buffer
