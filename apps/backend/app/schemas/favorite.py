from pydantic import BaseModel
from datetime import datetime
from typing import List


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    conversation_id: int
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class FavoriteListResponse(BaseModel):
    favorites: List[FavoriteResponse]

    model_config = {
        "from_attributes": True
    }
