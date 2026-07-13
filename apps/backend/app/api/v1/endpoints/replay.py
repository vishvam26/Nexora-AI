import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.models.message import Message
from app.schemas.rag_evaluation import SessionReplayResponse, DatasetExportResponse
from app.services.replay_service import ReplayService
from app.services.dataset_export_service import DatasetExportService

logger = logging.getLogger("app.api.replay")

router = APIRouter(prefix="/sessions", tags=["Session Replay & Dataset Export"])


@router.get(
    "/{id}/replay",
    response_model=SessionReplayResponse,
    summary="Replay message execution trace and metadata logs"
)
def get_session_replay(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 10: Session Replay
    Loads prompt variables, strategy decisions, latencies, tokens and citations.
    """
    return ReplayService.get_session_replay(db, id)


@router.get(
    "/export/dataset",
    response_model=DatasetExportResponse,
    summary="Export conversation logs into training datasets"
)
def export_dataset(
    conversation_id: int = Query(..., description="Conversation ID"),
    format: str = Query("sharegpt", description="Format choice: sharegpt, openai, alpaca"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 9: Continuous Learning Dataset Exporter
    Formulates instruction tuning inputs for Volume 3.
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found in this conversation")

    fmt = format.lower().strip()
    if fmt == "sharegpt":
        data = DatasetExportService.format_sharegpt(messages)
    elif fmt == "openai":
        data = DatasetExportService.format_openai(messages)
    elif fmt == "alpaca":
        data = DatasetExportService.format_alpaca(messages)
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Choose: sharegpt, openai, alpaca")

    return DatasetExportResponse(
        format=format,
        total_records=len(data),
        data=data
    )
