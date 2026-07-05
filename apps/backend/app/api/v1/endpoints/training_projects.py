import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.training_project import (
    TrainingProjectCreate,
    TrainingProjectResponse,
    TrainingRunResponse,
    TrainingLogResponse,
    TrainingArtifactResponse,
    GPUProfileResponse
)
from app.services.training_project_service import TrainingProjectService
from app.services.gpu_detection_service import GPUDetectionService
from app.services.lora_config_builder import LoraConfigBuilder
from app.services.training_config_builder import TrainingConfigBuilder
from app.services.huggingface_service import HuggingFaceService
from app.services.lora_merge_service import LoraMergeService
from app.services.gguf_export_service import GgufExportService

logger = logging.getLogger("app.api.training")

router = APIRouter(prefix="/training", tags=["Model Training Engine"])


@router.post(
    "/projects",
    response_model=TrainingProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Training Project"
)
def create_training_project(
    workspace_id: int = Query(..., description="Workspace ID"),
    schema: TrainingProjectCreate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 1: Create a new Training Project to manage fine-tuning configuration.
    """
    return TrainingProjectService.create_project(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=schema.name,
        base_model=schema.base_model
    )


@router.get(
    "/projects",
    response_model=List[TrainingProjectResponse],
    summary="List all Training Projects in a workspace"
)
def list_training_projects(
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return TrainingProjectService.list_projects(db, workspace_id)


@router.post(
    "/start",
    response_model=TrainingRunResponse,
    summary="Initiate a Model Fine-Tuning Run (QLoRA + Unsloth)"
)
def start_model_training(
    project_id: int = Query(...),
    dataset_id: int = Query(...),
    rank: int = Query(16),
    epochs: int = Query(3),
    preset: str = Query("balanced"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 7 & 9: Builds QLoRA config, training hyperparameters, validates them,
    and initiates asynchronous training worker.
    """
    project = TrainingProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Training Project not found")

    lora = LoraConfigBuilder.build_config(r=rank, lora_alpha=rank * 2)
    training = TrainingConfigBuilder.build_config(epochs=epochs, preset=preset)

    return TrainingProjectService.initiate_training_run(
        db=db,
        project_id=project_id,
        dataset_id=dataset_id,
        lora_config=lora,
        training_config=training
    )


@router.post(
    "/merge",
    summary="Merge LoRA Adapters into base model parameters"
)
def merge_lora_adapters(
    base_model: str = Query(..., description="HF repo base path"),
    adapter_path: str = Query(..., description="LoRA checkpoints output path"),
    output_path: str = Query(..., description="Output merged weights directory"),
    current_user: User = Depends(get_current_user),
):
    """
    Module 9: Merges trained PEFT adapters into FP16/BF16 base weights.
    """
    success = LoraMergeService.merge_adapter(base_model, adapter_path, output_path)
    if not success:
        raise HTTPException(status_code=500, detail="Adapter merge operation failed.")
    return {"status": "Success", "message": f"Successfully merged parameters to: {output_path}"}


@router.post(
    "/export/gguf",
    summary="Convert merged PyTorch weights to GGUF format and package Ollama Modelfile"
)
def export_model_gguf(
    model_dir: str = Query(..., description="Directory with PyTorch weights"),
    output_file: str = Query(..., description="Output GGUF filepath"),
    quantization: str = Query("Q4_K_M", description="Quantization choice"),
    current_user: User = Depends(get_current_user),
):
    """
    Module 10 & 11: Converts PyTorch models to GGUF and creates Modelfile configurations.
    """
    success = GgufExportService.export_to_gguf(model_dir, output_file, quantization)
    if not success:
        raise HTTPException(status_code=500, detail="GGUF conversion failed.")

    # Create matching Modelfile config template
    modelfile_path = output_file.replace(".gguf", ".Modelfile")
    manifest = GgufExportService.create_ollama_manifest(output_file, modelfile_path)

    return {
        "status": "Success",
        "gguf_path": output_file,
        "modelfile_path": modelfile_path,
        "manifest": manifest
    }


@router.post(
    "/publish/huggingface",
    summary="Push fine-tuned weights or GGUF files to Hugging Face Model Hub"
)
def publish_to_huggingface(
    repo_id: str = Query(..., description="Hugging Face repo identifier e.g., username/model-name"),
    token: str = Query(..., description="Hugging Face User Access Token"),
    folder_path: str = Query(..., description="Local folder with weights to upload"),
    current_user: User = Depends(get_current_user),
):
    """
    Module 1: Creates repository targets on HF Hub and pushes folder contents.
    """
    logged_in = HuggingFaceService.login(token)
    if not logged_in:
        raise HTTPException(status_code=401, detail="Hugging Face Hub API login failed.")

    # Create Repo
    repo_name = HuggingFaceService.create_hub_repository(token, repo_id)
    # Upload Folder
    pushed = HuggingFaceService.push_to_hub(token, repo_name, folder_path)
    if not pushed:
        raise HTTPException(status_code=500, detail="Failed to upload files to HuggingFace Hub.")

    return {"status": "Success", "repo_url": f"https://huggingface.co/{repo_name}"}


@router.get(
    "/gpu/profile",
    response_model=GPUProfileResponse,
    summary="Get CUDA and VRAM GPU hardware profile recommendations"
)
def get_gpu_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Module 8: GPU hardware profile check recommendations.
    """
    return GPUDetectionService.detect_gpu_resources()


@router.get(
    "/logs",
    response_model=List[TrainingLogResponse],
    summary="Get training metrics log list for a training run"
)
def get_training_logs(
    run_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 10: Live training metrics logs.
    """
    return TrainingProjectService.get_run_logs(db, run_id)


@router.get(
    "/artifacts",
    response_model=List[TrainingArtifactResponse],
    summary="Get output weights artifacts generated by a training run"
)
def get_training_artifacts(
    run_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 12: Catalogs output model weights adapters.
    """
    return TrainingProjectService.get_run_artifacts(db, run_id)
