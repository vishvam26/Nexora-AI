from pydantic import BaseModel, Field
from typing import Optional


class WorkspaceBrandingUpdate(BaseModel):
    logo_url: Optional[str] = Field(None, max_length=255)
    primary_color: Optional[str] = Field(None, max_length=7, description="HEX format, e.g. #4F46E5")
    accent_color: Optional[str] = Field(None, max_length=7, description="HEX format, e.g. #10B981")
    theme: Optional[str] = Field(None, max_length=20)
    welcome_message: Optional[str] = None
    banner_url: Optional[str] = Field(None, max_length=255)


class WorkspaceBrandingResponse(BaseModel):
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    theme: Optional[str] = None
    welcome_message: Optional[str] = None
    banner_url: Optional[str] = None

    model_config = {
        "from_attributes": True
    }
