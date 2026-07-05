import logging
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.rag_evaluation import BenchmarkResponse
from app.services.benchmark_service import BenchmarkService

logger = logging.getLogger("app.api.benchmark")

router = APIRouter(prefix="/benchmark", tags=["Retrieval Benchmark Framework"])


@router.get(
    "",
    response_model=BenchmarkResponse,
    summary="Compare Vector, Hybrid, Graph and Keyword strategies"
)
def run_retrieval_benchmark(
    query: str = Query(..., description="The query to test strategies"),
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 6: Retrieval Benchmark Leaderboard
    Executes all strategy algorithms on target query and reports latencies.
    """
    return BenchmarkService.run_benchmark(db, query, workspace_id)
