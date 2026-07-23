from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class TaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    status: str = "pending"
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskResponse(TaskBase):
    id: int
    workspace_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True


class WorkspaceProgressResponse(BaseModel):
    workspace_id: int
    total_tasks: int
    completed_tasks: int
    completion_percentage: float
    status_summary: dict
    estimated_completion_days: Optional[int] = None
    ai_status_recommendation: Optional[str] = None
