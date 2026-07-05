import re
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional

ALLOWED_COLORS = ["blue", "purple", "green", "orange", "gray", "red", "pink"]


class FolderCreate(BaseModel):
    workspace_id: int = Field(..., description="The ID of the workspace this folder belongs to")
    name: str = Field(..., description="The name of the folder")
    color: str = Field("Blue", description="Allowed: Blue, Purple, Green, Orange, Gray, Red, Pink or Hex (e.g. #FF5733)")
    icon: str = Field("📁", description="Emoji, Feather or Lucide icon string name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Folder name cannot be empty or blank")
        if len(value) < 1 or len(value) > 60:
            raise ValueError("Folder name must be between 1 and 60 characters")
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        value = value.strip()
        # Verify color name is in allowed lists (case-insensitive) or matches hex format
        if value.lower() in ALLOWED_COLORS:
            return value.capitalize()
        if re.match(r"^#[0-9a-fA-F]{6}$", value):
            return value
        raise ValueError(
            "Color must be one of: Blue, Purple, Green, Orange, Gray, Red, Pink or a valid 6-char Hex code starting with #"
        )


class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The name of the folder")
    color: Optional[str] = Field(None, description="Allowed: Blue, Purple, Green, Orange, Gray, Red, Pink or Hex")
    icon: Optional[str] = Field(None, description="Emoji, Feather or Lucide icon string name")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Folder name cannot be empty or blank")
        if len(value) < 1 or len(value) > 60:
            raise ValueError("Folder name must be between 1 and 60 characters")
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if value.lower() in ALLOWED_COLORS:
            return value.capitalize()
        if re.match(r"^#[0-9a-fA-F]{6}$", value):
            return value
        raise ValueError(
            "Color must be one of: Blue, Purple, Green, Orange, Gray, Red, Pink or a valid 6-char Hex code starting with #"
        )


class FolderResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    color: str
    icon: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class FolderListResponse(BaseModel):
    folders: List[FolderResponse]

    model_config = {
        "from_attributes": True
    }
