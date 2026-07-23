from pydantic import BaseModel, Field, field_validator, EmailStr
from datetime import datetime
from typing import List, Optional


class WorkspaceInvitationCreate(BaseModel):
    email: EmailStr = Field(..., description="The email address to invite")
    role: str = Field("EMPLOYEE", description="The role assigned to the invitation (MANAGER, EMPLOYEE)")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in ["MANAGER", "EMPLOYEE"]:
            raise ValueError("Invitation role must be one of: MANAGER, EMPLOYEE")
        return value


class AcceptInvitationRequest(BaseModel):
    token: str = Field(..., description="The unique UUID token sent in the invitation")


class DeclineInvitationRequest(BaseModel):
    token: str = Field(..., description="The unique UUID token sent in the invitation")


class WorkspaceInvitationResponse(BaseModel):
    id: int
    workspace_id: int
    email: str
    invited_by: int
    role: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime
    accepted_at: Optional[datetime]

    model_config = {
        "from_attributes": True
    }


class WorkspaceInvitationListResponse(BaseModel):
    invitations: List[WorkspaceInvitationResponse]

    model_config = {
        "from_attributes": True
    }
