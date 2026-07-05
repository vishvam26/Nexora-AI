"""
Agent Observability API Endpoints — Step 12

Routes:
  GET /agents/metrics        — Aggregated runtime stats & token cost calculations
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.agents.metrics_service import MetricsService

router = APIRouter(
    prefix="/agents",
    tags=["Agent Orchestration"],
)


@router.get(
    "/metrics",
    response_model=Dict[str, Any],
    summary="Retrieve multi-agent diagnostic logs & token cost summary statistics",
)
def get_diagnostics_metrics(
    current_user: User = Depends(get_current_user),
):
    """
    Scans the local agent session workspace directory:
    - Calculates overall success/failure rates
    - Compiles execution duration averages
    - Returns cumulative billing tracking metrics in USD (gpt-4o-mini rates)
    - Provides historical daily run timelines
    """
    return MetricsService.get_dashboard_data()
