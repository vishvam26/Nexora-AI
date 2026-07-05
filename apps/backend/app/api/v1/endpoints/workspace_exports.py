from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse, PlainTextResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.workspace_export_service import WorkspaceExportService
from typing import Optional

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace Import & Export"]
)


@router.get(
    "/{id}/export",
    status_code=status.HTTP_200_OK
)
def export_workspace_data(
    id: int,
    format: str = Query("json", description="Export format: json, md, html, zip"),
    folder_id: Optional[int] = Query(None, description="Scope export to single folder"),
    conversation_id: Optional[int] = Query(None, description="Scope export to single conversation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enterprise Export Engine: Packs messages, comments, reactions, and participants into JSON, MD, HTML or ZIP packages.
    """
    data = WorkspaceExportService.aggregate_data(
        db=db,
        user_id=current_user.id,
        workspace_id=id,
        folder_id=folder_id,
        conversation_id=conversation_id
    )

    format_lower = format.strip().lower()

    if format_lower == "json":
        return data
    elif format_lower == "md":
        md_text = WorkspaceExportService.render_markdown(data)
        return PlainTextResponse(md_text, media_type="text/markdown")
    elif format_lower == "html":
        html_text = WorkspaceExportService.render_html(data)
        return HTMLResponse(html_text)
    elif format_lower == "zip":
        zip_io = WorkspaceExportService.render_zip(data)
        filename = f"workspace_{id}_export.zip"
        return StreamingResponse(
            zip_io,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        # Fallback to JSON
        return data
