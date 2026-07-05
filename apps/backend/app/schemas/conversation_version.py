from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ConversationVersionResponse(BaseModel):
    id: int
    conversation_id: int
    before_content: str
    after_content: str
    editor_id: int
    reason: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ConversationVersionListResponse(BaseModel):
    versions: List[ConversationVersionResponse]
