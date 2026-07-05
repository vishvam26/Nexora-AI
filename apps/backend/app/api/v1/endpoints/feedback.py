import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.rag_evaluation import ChatFeedbackCreate, ChatFeedbackResponse, FeedbackAnalyticsResponse
from app.services.feedback_service import FeedbackService

logger = logging.getLogger("app.api.feedback")

router = APIRouter(prefix="/feedback", tags=["User Feedback Learning"])


@router.post(
    "",
    response_model=ChatFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user thumbs-up/down feedback on chat messages"
)
def submit_chat_feedback(
    schema: ChatFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits ratings or thumbs feedback details.
    """
    return FeedbackService.submit_feedback(
        db=db,
        user_id=current_user.id,
        conversation_id=schema.conversation_id,
        message_id=schema.message_id,
        rating=schema.rating,
        thumbs_up=schema.thumbs_up,
        thumbs_down=schema.thumbs_down,
        feedback=schema.feedback
    )


@router.get(
    "/analytics",
    response_model=FeedbackAnalyticsResponse,
    summary="Get chat feedback aggregated counters"
)
def get_feedback_analytics(
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return FeedbackService.get_feedback_analytics(db, workspace_id)
