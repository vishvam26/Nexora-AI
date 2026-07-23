from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class CompanyMemberResponse(BaseModel):
    id: int
    full_name: str
    email: str
    company_role: str
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class CompanyMemberUpdate(BaseModel):
    company_role: Optional[str] = None
    manager_id: Optional[int] = None


class CompanySettingsResponse(BaseModel):
    default_llm: str
    theme: str
    logo: Optional[str] = None
    max_file_size: int
    allowed_extensions: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CompanySettingsUpdate(BaseModel):
    default_llm: Optional[str] = None
    theme: Optional[str] = None
    logo: Optional[str] = None
    max_file_size: Optional[int] = None
    allowed_extensions: Optional[Dict[str, Any]] = None


class CompanySecretCreate(BaseModel):
    provider: str
    api_key: str


class CompanySecretResponse(BaseModel):
    id: int
    provider: str

    class Config:
        from_attributes = True


class CompanyInviteRequest(BaseModel):
    email: EmailStr
    role: str = "EMPLOYEE"  # ADMIN, EMPLOYEE


class CompanyInviteResponse(BaseModel):
    id: int
    email: str
    role: str
    token: str
    expires_at: datetime
    accepted: bool
    created_at: datetime

    class Config:
        from_attributes = True
