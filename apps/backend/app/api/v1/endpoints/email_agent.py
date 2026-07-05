"""
Email Sandbox endpoints — Step 15 Email Agent

Exposes routes to:
  - Compose HTML emails and dispatch them dynamically via SMTP
  - Attach previously generated PDF/Excel reports by ID
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.agents.email_agent import EmailAgent
from app.services.agents.base_agent import AgentContext, AgentResult
from app.schemas.email_agent import EmailSendRequest

router = APIRouter(
    prefix="/email",
    tags=["Email Sandbox"],
)

REPORT_DIR = os.path.join("storage", "reports")


@router.post(
    "/send",
    response_model=Dict[str, Any],
    summary="Compose and dispatch email envelopes securely via SMTP",
)
def send_envelope_email(
    payload: EmailSendRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Assembles multipart MIME envelopes and sends emails via SMTP connections.
    If report_id is supplied, it auto-discovers and attaches the matching report file.
    """
    agent = EmailAgent()
    context = AgentContext(
        question="Manual Email Dispatch Request"
    )

    # Inject the attachment file path into prior results if report_id exists
    if payload.report_id:
        report_subdir = os.path.join(REPORT_DIR, payload.report_id)
        # Find the primary file to attach
        priority_order = [".pdf", ".xlsx", ".pptx", ".png", ".md"]
        found_path = None
        for ext in priority_order:
            candidate = os.path.join(report_subdir, f"{payload.report_id}{ext}")
            if os.path.exists(candidate):
                found_path = candidate
                break

        if found_path:
            # Package as standard report_agent result mock context
            context.prior_results = {
                "report_agent": {
                    "export_path": found_path
                }
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report file for ID '{payload.report_id}' not found."
            )

    # Format SMTP instruction task syntax
    task = f"to: {payload.to_email}\nsubject: {payload.subject}\nbody: {payload.body}"
    res = agent.run(task, context)

    if res.status == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.error or "SMTP email dispatch crashed."
        )
    return res.output
