from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    workspace_id: int
    type: str
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]

    model_config = {
        "from_attributes": True
    }
