from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class CommentCreate(BaseModel):
    conversation_id: int = Field(..., description="The ID of the conversation to comment on")
    parent_comment_id: Optional[int] = Field(None, description="Optional parent comment ID for nested threads")
    content: str = Field(..., min_length=1, description="The comment text content")


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, description="The updated comment content")


class CommentResponse(BaseModel):
    id: int
    conversation_id: int
    user_id: int
    parent_comment_id: Optional[int] = None
    content: str
    edited_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    replies: List["CommentResponse"] = []

    model_config = {
        "from_attributes": True
    }


class CommentListResponse(BaseModel):
    comments: List[CommentResponse]

    model_config = {
        "from_attributes": True
    }
