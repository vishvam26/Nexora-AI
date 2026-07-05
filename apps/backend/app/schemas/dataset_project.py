from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    language: str = Field("English", max_length=50)
    visibility: str = Field("private", pattern="^(private|workspace|public)$")


class DatasetProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    language: str
    visibility: str
    created_by: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatasetVersionResponse(BaseModel):
    id: int
    project_id: int
    version_tag: str
    sample_count: int
    token_count: int
    storage_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetPreviewResponse(BaseModel):
    conversation_count: int
    message_count: int
    token_estimate: int
    estimated_cost_usd: float
    languages: List[str]


class DatasetValidationResponse(BaseModel):
    valid: bool
    errors: List[str]
    warnings: List[str]
    total_messages: int


class DatasetExportResponse(BaseModel):
    format: str
    total_records: int
    data: List[Dict[str, Any]]
