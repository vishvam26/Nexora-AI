from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class WorkspaceSettingsUpdate(BaseModel):
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=20)
    date_format: Optional[str] = Field(None, max_length=20)
    ai_model_preference: Optional[str] = Field(None, max_length=50)
    notification_preferences: Optional[Dict[str, Any]] = None
    guest_policy: Optional[str] = Field(None, max_length=20)
    sharing_policy: Optional[str] = Field(None, max_length=20)
    retention_period_days: Optional[int] = None
    auto_archive_days: Optional[int] = None
    history_size_limit: Optional[int] = None

    # Enterprise Policies
    disable_sharing: Optional[bool] = None
    disable_exports: Optional[bool] = None
    disable_public_links: Optional[bool] = None
    disable_invite: Optional[bool] = None
    disable_downloads: Optional[bool] = None
    disable_comments: Optional[bool] = None
    disable_reactions: Optional[bool] = None
    allowed_domains: Optional[str] = Field(None, max_length=255)

    # Metadata & Quotas
    plan: Optional[str] = Field(None, max_length=20)
    region: Optional[str] = Field(None, max_length=20)
    data_residency: Optional[str] = Field(None, max_length=20)
    organization: Optional[str] = Field(None, max_length=100)
    license_key: Optional[str] = Field(None, max_length=100)


class WorkspaceSettingsResponse(BaseModel):
    timezone: str
    language: str
    date_format: str
    ai_model_preference: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    guest_policy: str
    sharing_policy: str
    retention_period_days: Optional[int] = None
    auto_archive_days: Optional[int] = None
    history_size_limit: Optional[int] = None

    # Enterprise Policies
    disable_sharing: bool
    disable_exports: bool
    disable_public_links: bool
    disable_invite: bool
    disable_downloads: bool
    disable_comments: bool
    disable_reactions: bool
    allowed_domains: Optional[str] = None

    # Metadata & Quotas
    plan: str
    region: str
    data_residency: str
    organization: Optional[str] = None
    license_key: Optional[str] = None

    model_config = {
        "from_attributes": True
    }
