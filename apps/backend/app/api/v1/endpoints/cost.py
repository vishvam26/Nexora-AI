import logging
from fastapi import APIRouter, Depends, Query, status
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.rag_evaluation import CostEstimateResponse
from app.services.cost_service import CostService

logger = logging.getLogger("app.api.cost")

router = APIRouter(prefix="/cost", tags=["Cost Tracking"])


@router.get(
    "/estimate",
    response_model=CostEstimateResponse,
    summary="Estimate USD cost based on token counts"
)
def estimate_cost(
    prompt_tokens: int = Query(..., ge=0),
    completion_tokens: int = Query(..., ge=0),
    embedding_tokens: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """
    Module 11: Estimated USD API Costs calculations.
    """
    return CostService.calculate_cost(prompt_tokens, completion_tokens, embedding_tokens)
