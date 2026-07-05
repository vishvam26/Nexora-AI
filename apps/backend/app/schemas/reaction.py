from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List

ALLOWED_EMOJIS = ["👍", "❤️", "🔥", "🚀", "👏", "👀", "😂", "🤯"]


class ReactionCreate(BaseModel):
    emoji: str = Field(..., description="Allowed emojis: 👍, ❤️, 🔥, 🚀, 👏, 👀, 😂, 🤯")

    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, value: str) -> str:
        value = value.strip()
        if value not in ALLOWED_EMOJIS:
            raise ValueError(f"Emoji must be one of: {', '.join(ALLOWED_EMOJIS)}")
        return value


class ReactionResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    emoji: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ReactionListResponse(BaseModel):
    reactions: List[ReactionResponse]

    model_config = {
        "from_attributes": True
    }
