import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.dataset_project import (
    DatasetProjectCreate,
    DatasetProjectResponse,
    DatasetVersionResponse,
    DatasetPreviewResponse,
    DatasetValidationResponse,
    DatasetExportResponse
)
from app.services.dataset_project_service import DatasetProjectService
from app.services.dataset_collector_service import DatasetCollectorService
from app.services.dataset_validation_service import DatasetValidationService
from app.services.dataset_export_service import DatasetExportService
from app.services.language_detection_service import LanguageDetectionService

logger = logging.getLogger("app.api.datasets")

router = APIRouter(prefix="/datasets", tags=["AI Dataset Engineering Platform"])


@router.post(
    "/create",
    response_model=DatasetProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Dataset Project"
)
def create_dataset_project(
    workspace_id: int = Query(..., description="Workspace context"),
    schema: DatasetProjectCreate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 1: Create a new Dataset Project inside a Workspace.
    """
    return DatasetProjectService.create_project(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=schema.name,
        description=schema.description,
        language=schema.language,
        visibility=schema.visibility
    )


@router.get(
    "",
    response_model=List[DatasetProjectResponse],
    summary="List all Dataset Projects in a workspace"
)
def list_dataset_projects(
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DatasetProjectService.list_projects(db, workspace_id)


@router.get(
    "/{id}/preview",
    response_model=DatasetPreviewResponse,
    summary="Dry-run dry stats and token counts of target dataset conversations"
)
def preview_dataset(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 3: Preview engine mapping token estimates, sizes and languages before compiling exports.
    """
    project = DatasetProjectService.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Dataset Project not found")

    conversations = DatasetCollectorService.collect_conversations(db, project.workspace_id)
    conv_ids = [c.id for c in conversations]
    messages = DatasetCollectorService.get_messages_for_export(db, conv_ids)

    # Simple estimations
    msg_count = len(messages)
    text_content = " ".join(m.content for m in messages if m.content)
    token_est = len(text_content) // 4
    cost_est = (token_est / 1000) * 0.0015  # Mock GPT-3.5 token cost

    # Language detections
    detected_langs = list({LanguageDetectionService.detect_language(m.content) for m in messages if m.content})

    return DatasetPreviewResponse(
        conversation_count=len(conversations),
        message_count=msg_count,
        token_estimate=token_est,
        estimated_cost_usd=round(cost_est, 4),
        languages=detected_langs
    )


@router.post(
    "/{id}/validate",
    response_model=DatasetValidationResponse,
    summary="Validate dataset conversation sequence formats and empty messages"
)
def validate_dataset(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 18: Runs role validation, role alternation, and UTF checks prior to snapshotting.
    """
    project = DatasetProjectService.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Dataset Project not found")

    conversations = DatasetCollectorService.collect_conversations(db, project.workspace_id)
    conv_ids = [c.id for c in conversations]
    messages = DatasetCollectorService.get_messages_for_export(db, conv_ids)

    return DatasetValidationService.validate_messages(messages)


@router.post(
    "/{id}/export",
    response_model=DatasetExportResponse,
    summary="Run cleaning pipeline and export dataset formatting payloads"
)
def export_dataset(
    id: int,
    format: str = Query("sharegpt", description="Export choices: sharegpt, openai, alpaca, chatml"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 4, 5 & 15: Runs PII masking, exact cleaning, and formats results.
    """
    project = DatasetProjectService.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Dataset Project not found")

    conversations = DatasetCollectorService.collect_conversations(db, project.workspace_id)
    conv_ids = [c.id for c in conversations]
    messages = DatasetCollectorService.get_messages_for_export(db, conv_ids)

    # Clean and mask PII
    cleaned_messages = DatasetProjectService.run_cleaning_and_masking(messages)

    fmt = format.lower().strip()
    if fmt == "sharegpt":
        data = DatasetExportService.format_sharegpt(cleaned_messages)
    elif fmt == "openai":
        data = DatasetExportService.format_openai(cleaned_messages)
    elif fmt == "alpaca":
        data = DatasetExportService.format_alpaca(cleaned_messages)
    elif fmt == "chatml":
        chatml_str = DatasetExportService.format_chatml(cleaned_messages)
        data = [{"chatml": chatml_str}]
    else:
        raise HTTPException(status_code=400, detail="Invalid format selected")

    # Record snapshot metadata
    text_content = " ".join(m.content for m in cleaned_messages if m.content)
    token_est = len(text_content) // 4
    DatasetProjectService.create_version_snapshot(
        db=db,
        project_id=id,
        version_tag="v1.0.0",
        sample_count=len(data),
        token_count=token_est,
        storage_path=f"datasets/{id}/v1.0.0.jsonl"
    )

    return DatasetExportResponse(
        format=format,
        total_records=len(data),
        data=data
    )


@router.get(
    "/{id}/versions",
    response_model=List[DatasetVersionResponse],
    summary="List immutable snapshot versions of a dataset project"
)
def get_dataset_versions(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return DatasetProjectService.get_versions(db, id)
