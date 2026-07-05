from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TrainingProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    base_model: str = Field("Qwen/Qwen2.5-7B-Instruct", max_length=100)


class TrainingProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    base_model: str
    status: str
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainingRunResponse(BaseModel):
    id: int
    project_id: int
    dataset_project_id: int
    status: str
    lora_config: Optional[Dict[str, Any]]
    training_config: Optional[Dict[str, Any]]
    current_epoch: int
    current_step: int
    loss: Optional[float]
    gpu_usage_pct: Optional[float]
    vram_usage_gb: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainingLogResponse(BaseModel):
    id: int
    run_id: int
    step: int
    loss: float
    learning_rate: float
    tokens_per_sec: float
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainingArtifactResponse(BaseModel):
    id: int
    run_id: int
    artifact_type: str
    storage_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GPUProfileResponse(BaseModel):
    cuda_available: bool
    gpu_name: str
    vram_gb: float
    compute_capability: str
    supports_bf16: bool
    recommendations: Dict[str, Any]
