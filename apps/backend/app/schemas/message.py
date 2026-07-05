from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Literal, Optional


class MessageCreate(BaseModel):
    """
    Schema for creating a new Message.
    """
    conversation_id: int = Field(
        ...,
        description="The ID of the conversation this message belongs to"
    )
    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="The role of the message sender: 'user', 'assistant', or 'system'"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="The text content of the message"
    )


class MessageResponse(BaseModel):
    """
    Schema for full Message details in responses.
    """
    id: int
    conversation_id: int
    role: str
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class MessageListResponse(BaseModel):
    """
    Schema representing a list of conversation messages.
    """
    messages: List[MessageResponse]

    model_config = {
        "from_attributes": True
    }


class MessageUpdate(BaseModel):
    content: str = Field(..., min_length=1)
    reason: Optional[str] = None

