from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: str = Field(default="📚", max_length=50)
    color: str = Field(default="#10B981", max_length=7)
    visibility: str = Field(default="private", pattern="^(private|workspace|public)$")


class KnowledgeBaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=7)
    visibility: Optional[str] = Field(None, pattern="^(private|workspace|public)$")


class KnowledgeBaseResponse(BaseModel):
    id: int
    uuid: str
    workspace_id: int
    title: str
    description: Optional[str]
    icon: str
    color: str
    visibility: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseListResponse(BaseModel):
    knowledge_bases: List[KnowledgeBaseResponse]
    total: int

    model_config = {"from_attributes": True}
