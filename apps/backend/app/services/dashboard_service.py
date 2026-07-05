import logging
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.folder import Folder
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.models.notification import Notification
from app.models.favorite import Favorite
from app.models.conversation_comment import ConversationComment
from app.schemas.dashboard import DashboardResponse, DashboardAnalytics
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

logger = logging.getLogger("app.services.dashboard_service")


class DashboardService:
    """
    Service layer executing optimized aggregations to construct the Workspace Dashboard Analytics.
    Optimized to prevent N+1 query patterns.
    """

    @staticmethod
    def compile_dashboard(db: Session, user_id: int, workspace_id: int) -> DashboardResponse:
        """
        Gathers workspace metrics and aggregates analytics. Enforces view permissions and logs access.
        """
        # Enforce workspace view permission
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")

        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        # 1. Base counts using optimized aggregate counts
        members_count = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).count()

        folders_count = db.query(Folder).filter(
            Folder.workspace_id == workspace_id,
            Folder.deleted_at.is_(None)
        ).count()

        convo_query = db.query(Conversation).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False
        )
        conversations_count = convo_query.count()
        pinned_count = convo_query.filter(Conversation.is_pinned == True).count()
        archived_count = convo_query.filter(Conversation.is_archived == True).count()

        convo_ids_subquery = db.query(Conversation.id).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False
        ).subquery()

        messages_query = db.query(Message).filter(
            Message.conversation_id.in_(convo_ids_subquery),
            Message.is_deleted == False
        )
        messages_count = messages_query.count()

        ai_requests_count = messages_query.filter(Message.role == "assistant").count()

        # 2. Activity count and notifications
        today_activity_count = db.query(ActivityLog).filter(
            ActivityLog.workspace_id == workspace_id,
            ActivityLog.created_at >= today_start
        ).count()

        unread_notifications_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.workspace_id == workspace_id,
            Notification.is_read == False
        ).count()

        favorites_count = db.query(Favorite).join(Conversation).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False,
            Favorite.user_id == user_id
        ).count()

        # 3. Recent members
        recent_member_users = db.query(User.full_name).join(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.is_active == True
        ).order_by(WorkspaceMember.joined_at.desc()).limit(5).all()
        recent_members = [m[0] for m in recent_member_users]

        # 4. Storage size calculations (aggregate sum of content sizes)
        convo_titles_length = db.query(func.sum(func.length(Conversation.title))).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False
        ).scalar() or 0

        msg_contents_length = db.query(func.sum(func.length(Message.content))).filter(
            Message.conversation_id.in_(convo_ids_subquery),
            Message.is_deleted == False
        ).scalar() or 0

        comment_contents_length = db.query(func.sum(func.length(ConversationComment.content))).filter(
            ConversationComment.conversation_id.in_(convo_ids_subquery),
            ConversationComment.deleted_at.is_(None)
        ).scalar() or 0

        storage_usage = convo_titles_length + msg_contents_length + comment_contents_length

        # 5. Message frequencies (Today, Week, Month)
        msg_today = messages_query.filter(Message.created_at >= today_start).count()
        msg_week = messages_query.filter(Message.created_at >= week_start).count()
        msg_month = messages_query.filter(Message.created_at >= month_start).count()

        # 6. Average conversation length
        avg_convo_len = 0.0
        if conversations_count > 0:
            avg_convo_len = float(messages_count) / conversations_count

        # 7. Average Response Time calculation (Time delta between User -> Assistant responses)
        avg_res_time = 0.0
        responses = messages_query.filter(Message.role == "assistant").order_by(Message.created_at.asc()).all()
        delta_sums = 0.0
        delta_count = 0
        for resp in responses:
            # Find the user prompt immediately preceding this response in the same chat
            prev_user_msg = db.query(Message).filter(
                Message.conversation_id == resp.conversation_id,
                Message.role == "user",
                Message.created_at < resp.created_at,
                Message.is_deleted == False
            ).order_by(Message.created_at.desc()).first()

            if prev_user_msg:
                delta_sums += (resp.created_at - prev_user_msg.created_at).total_seconds()
                delta_count += 1

        if delta_count > 0:
            avg_res_time = delta_sums / delta_count

        # 8. Most Active Member (by message count)
        most_active_member = None
        active_user_query = db.query(
            User.full_name, func.count(Message.id).label("cnt")
        ).join(Message, Message.user_id == User.id).filter(
            Message.conversation_id.in_(convo_ids_subquery),
            Message.is_deleted == False
        ).group_by(User.id, User.full_name).order_by(sa.desc("cnt")).first()

        if active_user_query:
            most_active_member = active_user_query[0]

        # 9. Most Used Folder (by conversation count)
        most_used_folder = None
        used_folder_query = db.query(
            Folder.name, func.count(Conversation.id).label("cnt")
        ).join(Conversation, Conversation.folder_id == Folder.id).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False
        ).group_by(Folder.id, Folder.name).order_by(sa.desc("cnt")).first()

        if used_folder_query:
            most_used_folder = used_folder_query[0]

        # 10. Top Conversation (by message count)
        top_conversation = None
        top_convo_query = db.query(
            Conversation.title, func.count(Message.id).label("cnt")
        ).join(Message, Message.conversation_id == Conversation.id).filter(
            Conversation.workspace_id == workspace_id,
            Conversation.is_deleted == False,
            Message.is_deleted == False
        ).group_by(Conversation.id, Conversation.title).order_by(sa.desc("cnt")).first()

        if top_convo_query:
            top_conversation = top_convo_query[0]

        # Log Activity
        ActivityService.log_activity(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action="Dashboard Viewed",
            entity="Workspace",
            entity_id=workspace_id
        )

        analytics = DashboardAnalytics(
            messages_today=msg_today,
            messages_this_week=msg_week,
            messages_this_month=msg_month,
            average_conversation_length=round(avg_convo_len, 2),
            average_response_time=round(avg_res_time, 2),
            most_active_member=most_active_member,
            most_used_folder=most_used_folder,
            top_conversation=top_conversation
        )

        return DashboardResponse(
            workspace_name=workspace.name,
            members_count=members_count,
            folders_count=folders_count,
            conversations_count=conversations_count,
            messages_count=messages_count,
            ai_requests_count=ai_requests_count,
            today_activity_count=today_activity_count,
            unread_notifications_count=unread_notifications_count,
            favorites_count=favorites_count,
            pinned_conversations_count=pinned_count,
            archived_conversations_count=archived_count,
            recent_members=recent_members,
            storage_usage_bytes=storage_usage,
            analytics=analytics
        )
