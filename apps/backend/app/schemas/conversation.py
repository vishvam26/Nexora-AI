from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class ConversationCreate(BaseModel):
    """
    Schema for creating a new Conversation.
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="The title of the conversation"
    )
    workspace_id: Optional[int] = Field(
        None,
        description="The optional workspace ID containing this conversation"
    )
    folder_id: Optional[int] = Field(
        None,
        description="The optional folder ID inside the workspace"
    )


class ConversationResponse(BaseModel):
    """
    Schema for full Conversation response details.
    """
    id: int
    user_id: int
    workspace_id: Optional[int] = None
    folder_id: Optional[int] = None
    title: str
    summary: Optional[str] = None
    position: int = 0
    is_pinned: bool = False
    is_archived: bool = False
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ConversationListResponse(BaseModel):
    """
    Schema for listing active Conversations.
    """
    conversations: List[ConversationResponse]

    model_config = {
        "from_attributes": True
    }


class ConversationMove(BaseModel):
    """
    Input schema for moving a conversation to a folder.
    """
    folder_id: Optional[int] = Field(None, description="The target folder ID (or null to move out)")


class ConversationStatsResponse(BaseModel):
    """
    Statistics for a single conversation.
    """
    messages_count: int
    created_at: datetime
    updated_at: datetime
    is_pinned: bool
    is_archived: bool


class WorkspaceStatsResponse(BaseModel):
    """
    Statistics for a workspace.
    """
    folders_count: int
    conversations_count: int
    messages_count: int
    last_active: Optional[datetime]


class MessageSearchMatch(BaseModel):
    """
    Serialized match information for a message.
    """
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class SearchResult(BaseModel):
    """
    Single query result containing conversation details and optionally matching messages.
    """
    conversation: ConversationResponse
    matched_messages: List[MessageSearchMatch] = []


class SearchResponse(BaseModel):
    """
    Consolidated global query search response with pagination bounds.
    """
    results: List[SearchResult]
    limit: int
    offset: int
    total: int


class ConversationShareRequest(BaseModel):
    """
    Request body for conversation sharing.
    Allowed values for expires_in: "never", "24h", "7d", "30d"
    """
    expires_in: Optional[str] = Field("never", description="Expiry period: never, 24h, 7d, 30d")


class ConversationShareResponse(BaseModel):
    """
    Response details for conversation sharing request.
    """
    share_token: str
    share_url: str
    expires_at: Optional[datetime] = None


class SharedMessageResponse(BaseModel):
    """
    Simplified message representation for public shared views.
    """
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class SharedConversationResponse(BaseModel):
    """
    Complete public read-only conversation detail containing message logs.
    """
    id: int
    title: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[SharedMessageResponse]

    model_config = {
        "from_attributes": True
    }

