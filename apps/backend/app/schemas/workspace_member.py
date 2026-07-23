from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    workspace_role: str
    joined_at: datetime
    last_active: Optional[datetime]
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class WorkspaceMemberRoleUpdate(BaseModel):
    workspace_role: str = Field(..., description="The role to assign (MANAGER, EMPLOYEE)")

    @field_validator("workspace_role")
    @classmethod
    def validate_workspace_role(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ["MANAGER", "EMPLOYEE"]:
            raise ValueError("Role must be one of: MANAGER, EMPLOYEE")
        return value


class WorkspaceOwnershipTransfer(BaseModel):
    target_user_id: int = Field(..., description="The ID of the existing workspace manager to transfer ownership to")
