from pydantic import BaseModel
from typing import List, Optional


class DashboardAnalytics(BaseModel):
    messages_today: int
    messages_this_week: int
    messages_this_month: int
    average_conversation_length: float
    average_response_time: float  # in seconds
    most_active_member: Optional[str] = None
    most_used_folder: Optional[str] = None
    top_conversation: Optional[str] = None


class DashboardResponse(BaseModel):
    workspace_name: str
    members_count: int
    folders_count: int
    conversations_count: int
    messages_count: int
    ai_requests_count: int
    today_activity_count: int
    unread_notifications_count: int
    favorites_count: int
    pinned_conversations_count: int
    archived_conversations_count: int
    recent_members: List[str]  # names of recent members
    storage_usage_bytes: int
    active_sessions_count: int
    workspace_cost_usd: float
    analytics: DashboardAnalytics
