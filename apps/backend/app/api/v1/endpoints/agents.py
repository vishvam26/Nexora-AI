"""
Agent Orchestration API Endpoints — Step 11

Routes:
  POST /agents/ask                — Synchronous: full orchestration, returns complete session
  GET  /agents/stream             — SSE streaming: yields events per agent step (query params)
  GET  /agents/session/{id}       — Retrieve past session by ID
  GET  /agents/sessions           — List recent sessions (index)

Design:
  - /ask is the standard REST call (frontend can poll for status)
  - /stream uses Server-Sent Events for real-time AgentStudio pipeline animation
  - Both /ask and /stream require workspace_id or doc_id to be useful
  - File path resolution happens here (DB lookup) before passing to orchestrator
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services.agents.agent_orchestrator import get_orchestrator
from app.services.agents.agent_session import AgentSession
from app.schemas.agents import AgentAskRequest, AgentSessionResponse, AgentSessionSummary

router = APIRouter(
    prefix="/agents",
    tags=["Agent Orchestration"],
)

logger = logging.getLogger("app.api.v1.endpoints.agents")


def _resolve_file_path(db: Session, doc_id: Optional[int]) -> Optional[str]:
    """Looks up a document's storage_path from the DB given a doc_id."""
    if not doc_id:
        return None
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        return None
    return doc.storage_path


@router.post(
    "/ask",
    response_model=AgentSessionResponse,
    summary="Ask the Multi-Agent System a decision question (synchronous)",
)
def ask_agents(
    payload: AgentAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full synchronous orchestration pipeline:
    1. Manager Agent plans which agents to invoke
    2. Specialized agents execute sequentially
    3. Manager synthesizes final answer from all results
    4. Returns complete session with plan, agent results, final answer, and citations

    Typical latency: 5–30 seconds depending on number of agents invoked.
    For real-time UI feedback, use GET /agents/stream instead.
    """
    if not payload.workspace_id and not payload.doc_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: workspace_id (for RAG) or doc_id (for Analytics/ML).",
        )

    file_path = _resolve_file_path(db, payload.doc_id)

    orchestrator = get_orchestrator()
    try:
        session = orchestrator.ask(
            question=payload.question,
            workspace_id=payload.workspace_id,
            doc_id=payload.doc_id,
            file_path=file_path,
            top_k=payload.top_k,
            generate_report=payload.generate_report,
            report_format=payload.report_format,
            report_type=payload.report_type,
        )
        return session
    except Exception as e:
        logger.error(f"[agents/ask] Orchestration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent orchestration failed: {str(e)}",
        )


@router.get(
    "/stream",
    summary="Ask the Multi-Agent System (SSE streaming — real-time pipeline events)",
)
def ask_agents_stream(
    question: str = Query(..., description="CEO's decision question"),
    workspace_id: Optional[int] = Query(None, description="Workspace ID for RAG"),
    doc_id: Optional[int] = Query(None, description="Document ID for Analytics/ML"),
    top_k: int = Query(5, ge=1, le=20),
    generate_report: bool = Query(False),
    report_format: str = Query("pdf"),
    report_type: str = Query("full_analytics"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Server-Sent Events (SSE) streaming variant.
    Yields one event per agent step so the AgentStudio UI can animate in real-time.

    Event types:
      plan_ready       — Manager's execution plan
      agent_start      — An agent has started running
      agent_result     — An agent completed (summary + status + latency)
      synthesis_start  — All agents done, Manager is synthesizing
      final_answer     — Final answer + citations + confidence
      done             — Session complete + session_id for replay
    """
    if not workspace_id and not doc_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: workspace_id or doc_id.",
        )

    file_path = _resolve_file_path(db, doc_id)
    orchestrator = get_orchestrator()

    def event_generator():
        try:
            yield from orchestrator.ask_stream(
                question=question,
                workspace_id=workspace_id,
                doc_id=doc_id,
                file_path=file_path,
                top_k=top_k,
                generate_report=generate_report,
                report_format=report_format,
                report_type=report_type,
            )
        except Exception as e:
            import json
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable nginx buffering for SSE
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/session/{session_id}",
    response_model=AgentSessionResponse,
    summary="Retrieve a past agent session by ID",
)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the full session data for a previous orchestration run.
    Useful for replaying or auditing past agent decisions.
    """
    session = AgentSession.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return session


@router.get(
    "/sessions",
    summary="List recent agent orchestration sessions",
)
def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a compact list of recent sessions (from the index).
    Does NOT load full session data — use /session/{id} for full details.
    """
    return AgentSession.list_recent(limit=limit)
