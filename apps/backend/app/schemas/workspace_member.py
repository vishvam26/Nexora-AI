from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    role: str
    joined_at: datetime
    last_active: Optional[datetime]
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class WorkspaceMemberRoleUpdate(BaseModel):
    role: str = Field(..., description="The role to assign (ADMIN, EDITOR, VIEWER)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ["ADMIN", "EDITOR", "VIEWER"]:
            raise ValueError("Role must be one of: ADMIN, EDITOR, VIEWER")
        return value


class WorkspaceOwnershipTransfer(BaseModel):
    target_user_id: int = Field(..., description="The ID of the existing workspace admin to transfer ownership to")
