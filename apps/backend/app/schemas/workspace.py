import re
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional


class WorkspaceCreate(BaseModel):
    name: str = Field(..., description="The name of the workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Optional workspace description")
    icon: str = Field("💼", description="Emoji or predefined icon ID")
    color: str = Field("#4F46E5", description="Hex color code (e.g. #4F46E5)")
    visibility: str = Field("private", description="Workspace visibility: private, team, public")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Workspace name cannot be blank or only spaces")
        if len(value) < 3 or len(value) > 60:
            raise ValueError("Workspace name must be between 3 and 60 characters")
        if not any(char.isalnum() for char in value):
            raise ValueError("Workspace name must contain at least one alphanumeric character (cannot be only emojis or punctuation)")
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        value = value.strip()
        if not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValueError("Color must be a valid 6-character hex color code starting with # (e.g. #4F46E5)")
        return value

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, value: str) -> str:
        value = value.strip().lower()
        if value not in ["private", "team", "public"]:
            raise ValueError("Visibility must be one of: private, team, public")
        return value


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="The name of the workspace")
    description: Optional[str] = Field(None, max_length=1000, description="Optional workspace description")
    icon: Optional[str] = Field(None, description="Emoji or predefined icon ID")
    color: Optional[str] = Field(None, description="Hex color code")
    visibility: Optional[str] = Field(None, description="Workspace visibility: private, team, public")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Workspace name cannot be blank or only spaces")
        if len(value) < 3 or len(value) > 60:
            raise ValueError("Workspace name must be between 3 and 60 characters")
        if not any(char.isalnum() for char in value):
            raise ValueError("Workspace name must contain at least one alphanumeric character (cannot be only emojis or punctuation)")
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not re.match(r"^#[0-9a-fA-F]{6}$", value):
            raise ValueError("Color must be a valid 6-character hex color code starting with # (e.g. #4F46E5)")
        return value

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip().lower()
        if value not in ["private", "team", "public"]:
            raise ValueError("Visibility must be one of: private, team, public")
        return value


class WorkspaceResponse(BaseModel):
    id: int
    uuid: str
    owner_id: int
    name: str
    description: Optional[str]
    icon: str
    color: str
    visibility: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]

    model_config = {
        "from_attributes": True
    }


class ActiveWorkspaceRequest(BaseModel):
    workspace_id: int
