from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


class WorkspaceTemplateCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = Field(..., max_length=50)
    thumbnail: Optional[str] = None
    configuration: Dict[str, Any] = Field(..., description="Configuration dict to replicate workspace setup")
    is_public: bool = True


class WorkspaceTemplateResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    thumbnail: Optional[str]
    configuration: Dict[str, Any]
    is_public: bool
    owner_id: Optional[int]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class WorkspaceTemplateListResponse(BaseModel):
    templates: List[WorkspaceTemplateResponse]
