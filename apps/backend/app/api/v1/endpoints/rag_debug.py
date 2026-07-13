import logging
import time
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.query_service import QueryService
from app.services.context_strategy import ContextStrategyEngine
from app.services.adaptive_retrieval_service import AdaptiveRetrievalService
from app.schemas.analytics import RAGDebugBreakdown

logger = logging.getLogger("app.api.rag_debug")

router = APIRouter(prefix="/rag", tags=["RAG Debugging"])


@router.get(
    "/debug",
    response_model=RAGDebugBreakdown,
    summary="Get execution breakdown trace of RAG retrieval steps"
)
def get_rag_debug_trace(
    query: str = Query(..., description="The query to dry-run"),
    workspace_id: int = Query(..., description="Workspace context"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Module 15: RAG Debug Mode
    Performs dry-run context retrieval mapping latencies, character sizes, and tokens.
    """
    start_time = time.monotonic()

    classification = QueryService.classify(query)
    intent = classification["category"]
    strategy = ContextStrategyEngine.determine_strategy(intent)

    # Dry run search
    context = AdaptiveRetrievalService.retrieve_context(
        db=db,
        user_query=query,
        workspace_id=workspace_id,
        enable_reranking=True,
    )

    latency_ms = (time.monotonic() - start_time) * 1000
    char_size = len(context.formatted_context)
    token_est = char_size // 4

    return RAGDebugBreakdown(
        query=query,
        intent=intent,
        strategy=strategy,
        confidence_score=context.confidence_score,
        latency_ms=round(latency_ms, 2),
        chunks_retrieved=context.metrics.retrieved_count + context.metrics.dropped_count,
        chunks_accepted=context.metrics.retrieved_count,
        chunks_rejected=context.metrics.dropped_count,
        raw_context_size_chars=char_size,
        token_estimate=token_est
    )
