from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.message import MessageResponse


class ChatRequest(BaseModel):
    """
    Schema representing a chat prompt request.
    """
    conversation_id: int = Field(
        ...,
        description="The ID of the conversation to post the message to"
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The message prompt content to send to the AI"
    )
    workspace_id: Optional[int] = Field(
        None,
        description="Workspace ID for scoped RAG knowledge retrieval"
    )
    knowledge_base_id: Optional[int] = Field(
        None,
        description="Optional Knowledge Base ID to narrow RAG retrieval scope"
    )
    knowledge_base_ids: Optional[list] = Field(
        None,
        description="Optional list of Knowledge Base IDs for multi-KB retrieval"
    )
    grounded: bool = Field(
        True,
        description="Toggle grounding / RAG mode on or off"
    )


class ChatResponse(BaseModel):
    """
    Schema representing the conversation response containing user and AI responses.
    """
    user_message: MessageResponse = Field(
        ...,
        description="The saved user message object"
    )
    assistant_message: MessageResponse = Field(
        ...,
        description="The saved assistant message object"
    )
    conversation_id: int = Field(
        ...,
        description="The ID of the conversation"
    )

    model_config = {
        "from_attributes": True
    }
