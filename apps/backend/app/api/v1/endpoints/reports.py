"""
Report Generator API Endpoints — Step 10

Routes:
  POST /reports/generate/{doc_id}     — Generate a new AI report
  GET  /reports/list/{doc_id}         — List all generated reports for a document
  GET  /reports/download/{report_id}  — Download an exported report file

Design:
  - ReportService is the only orchestration layer; this file is thin REST glue
  - download endpoint returns the file directly using FileResponse
  - All endpoints require authentication via get_current_user
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services.report.report_service import ReportService
from app.schemas.report import ReportGenerateRequest

router = APIRouter(
    prefix="/reports",
    tags=["Report Generator"],
)

REPORT_DIR = os.path.join("storage", "reports")

# MIME type mapping for download headers
FORMAT_MIME = {
    "pdf": "application/pdf",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "png": "image/png",
    "markdown": "text/markdown",
}

FORMAT_EXT = {
    "pdf": ".pdf",
    "excel": ".xlsx",
    "pptx": ".pptx",
    "png": ".png",
    "markdown": ".md",
}


@router.post(
    "/generate/{doc_id}",
    response_model=Dict[str, Any],
    summary="Generate an AI-powered report for a document",
)
def generate_report(
    doc_id: int,
    payload: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full report generation pipeline:
    1. DataCollectorAgent gathers analytics + ML session + SHAP data
    2. PromptBuilder assembles a grounded LLM prompt (injection-safe)
    3. LLM generates narrative markdown
    4. ReportAssembler exports to requested format (PDF/Excel/PPTX/PNG/Markdown)

    Returns report metadata including export path and AI narrative.
    """
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        result = ReportService.generate(
            doc_id=doc_id,
            file_path=doc.storage_path,
            report_type=payload.report_type,
            export_format=payload.export_format,
            grounded=payload.grounded,
            custom_instructions=payload.custom_instructions or "",
            include_analytics=payload.include_analytics,
            include_ml=payload.include_ml,
            include_shap=payload.include_shap,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )


@router.get(
    "/list/{doc_id}",
    response_model=List[Dict[str, Any]],
    summary="List all generated reports for a document",
)
def list_reports(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a list of report metadata dicts (newest first).
    Does not include the full narrative to keep the response compact.
    """
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return ReportService.list_reports(doc_id)


@router.get(
    "/download/{report_id}",
    summary="Download a previously generated report file",
)
def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Downloads the exported report file by report_id.
    Supports all formats: PDF, Excel, PPTX, PNG, Markdown.
    Scans the report subdirectory for any matching file.
    """
    report_subdir = os.path.join(REPORT_DIR, report_id)
    if not os.path.isdir(report_subdir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found. Generate a report first.",
        )

    # Find the primary file (prefer non-.md if multiple formats exist)
    priority_order = [".pdf", ".xlsx", ".pptx", ".png", ".md", "_fallback.txt"]
    found_path = None
    for ext in priority_order:
        candidate = os.path.join(report_subdir, f"{report_id}{ext}")
        if os.path.exists(candidate):
            found_path = candidate
            break

    if not found_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No exported file found for report '{report_id}'.",
        )

    ext = os.path.splitext(found_path)[1].lower()
    fmt_map = {
        ".pdf": "application/pdf",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".png": "image/png",
        ".md": "text/markdown",
        ".txt": "text/plain",
    }
    media_type = fmt_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=found_path,
        media_type=media_type,
        filename=os.path.basename(found_path),
    )
