"""
Python Sandbox endpoints — Step 14 Python Execution Agent

Exposes routes to:
  - Run custom data analysis python scripts (Pandas, Matplotlib)
  - Return stdout log streams and relative static URLs of generated chart plots
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services.agents.python_agent import PythonAgent
from app.services.agents.base_agent import AgentContext
from app.schemas.python_agent import PythonCodeRequest
from app.security.limiter import limiter

router = APIRouter(
    prefix="/python",
    tags=["Python Sandbox"],
)


@router.post(
    "/execute/{doc_id}",
    response_model=Dict[str, Any],
    summary="Execute data analysis scripts against a document dynamically inside the sandbox",
)
@limiter.limit("5/minute")
def execute_python_code(
    request: Request,
    doc_id: int,
    payload: PythonCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    """
    Executes Python scripts (Pandas, Matplotlib) against the specified tabular document.
    Blocks import access to dangerous standard modules (os, sys, subprocess).
    """
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    agent = PythonAgent()
    context = AgentContext(
        question="Manual Execution Query",
        doc_id=doc_id,
        file_path=doc.storage_path
    )

    res = agent.run(payload.code, context)
    if res.status == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.error or "Sandbox execution failed."
        )
    return res.output
