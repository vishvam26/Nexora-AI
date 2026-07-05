from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceListResponse,
    ActiveWorkspaceRequest
)
from app.schemas.workspace_branding import WorkspaceBrandingResponse, WorkspaceBrandingUpdate
from app.schemas.workspace_settings import WorkspaceSettingsResponse, WorkspaceSettingsUpdate
from app.schemas.conversation import WorkspaceStatsResponse
from app.services.workspace_service import WorkspaceService
from app.services.conversation_service import ConversationService


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"]
)


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED
)
def create_workspace(
    request: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new Workspace for the authenticated user.
    """
    return WorkspaceService.create(db, current_user.id, request)


@router.get(
    "",
    response_model=WorkspaceListResponse,
    status_code=status.HTTP_200_OK
)
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all active workspaces belonging to the authenticated user.
    """
    workspaces = WorkspaceService.list_for_user(db, current_user.id)
    return WorkspaceListResponse(workspaces=workspaces)


@router.get(
    "/{id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK
)
def get_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the details of a specific workspace.
    """
    return WorkspaceService.get_workspace_with_ownership(db, current_user.id, id)


@router.patch(
    "/{id}",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK
)
def update_workspace(
    id: int,
    request: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Renames or updates properties of a specific workspace.
    """
    return WorkspaceService.update(db, current_user.id, id, request)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft deletes a specific workspace.
    """
    WorkspaceService.delete(db, current_user.id, id)
    return None


@router.post(
    "/active",
    status_code=status.HTTP_200_OK
)
def set_active_workspace(
    request: ActiveWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Placeholder endpoint to set the active workspace context.
    """
    # Validate workspace existence and ownership
    WorkspaceService.get_workspace_with_ownership(db, current_user.id, request.workspace_id)
    return {
        "status": "success",
        "active_workspace_id": request.workspace_id
    }


@router.get(
    "/{id}/stats",
    response_model=WorkspaceStatsResponse,
    status_code=status.HTTP_200_OK
)
def get_workspace_stats(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compiles and returns stats metadata for a workspace.
    """
    return ConversationService.get_workspace_stats(db, current_user.id, id)


@router.patch(
    "/{id}/branding",
    response_model=WorkspaceBrandingResponse,
    status_code=status.HTTP_200_OK
)
def update_workspace_branding(
    id: int,
    request: WorkspaceBrandingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the workspace branding theme colors, custom welcome message, banners and logos.
    """
    ws = WorkspaceService.update_branding(db, current_user.id, id, request.model_dump(exclude_unset=True))
    return WorkspaceBrandingResponse.model_validate(ws)


@router.patch(
    "/{id}/settings",
    response_model=WorkspaceSettingsResponse,
    status_code=status.HTTP_200_OK
)
def update_workspace_settings(
    id: int,
    request: WorkspaceSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates enterprise settings, policies, timezone configurations, retention periods and visibility.
    """
    ws = WorkspaceService.update_settings(db, current_user.id, id, request.model_dump(exclude_unset=True))
    return WorkspaceSettingsResponse.model_validate(ws)


@router.get(
    "/{id}/trash",
    status_code=status.HTTP_200_OK
)
def get_workspace_trash(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of soft-deleted assets (folders and conversations) waiting inside the Recycle Bin.
    """
    trash = WorkspaceService.get_trash(db, current_user.id, id)
    # Validate schemas manually or map into clean lists
    from app.schemas.folder import FolderResponse
    from app.schemas.conversation import ConversationResponse
    return {
        "folders": [FolderResponse.model_validate(f) for f in trash["folders"]],
        "conversations": [ConversationResponse.model_validate(c) for c in trash["conversations"]]
    }


@router.post(
    "/{id}/restore",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_200_OK
)
def restore_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restores a soft-deleted workspace back to active status. Only Owner role allowed.
    """
    return WorkspaceService.restore_workspace(db, current_user.id, id)


@router.delete(
    "/{id}/purge",
    status_code=status.HTTP_204_NO_CONTENT
)
def purge_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes a workspace from the database. Only Owner allowed.
    """
    WorkspaceService.purge_workspace(db, current_user.id, id)
    return None


@router.post(
    "/{id}/snapshot",
    status_code=status.HTTP_200_OK
)
def create_workspace_snapshot(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves a structural configuration state snapshot of folders and chat configurations.
    """
    return WorkspaceService.create_snapshot(db, current_user.id, id)


@router.post(
    "/{id}/backup",
    status_code=status.HTTP_200_OK
)
def backup_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Packs all conversations and folders inside a downloadable ZIP backup package.
    """
    from app.services.workspace_export_service import WorkspaceExportService
    data = WorkspaceExportService.aggregate_data(db, current_user.id, id)
    zip_io = WorkspaceExportService.render_zip(data)
    filename = f"workspace_{id}_backup.zip"
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        zip_io,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/{id}/replay",
    status_code=status.HTTP_200_OK
)
def activity_timeline_replay(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns audit timeline tracking everything from workspace creation, members joining, folder creations, and comments.
    """
    replay_logs = WorkspaceService.activity_replay(db, current_user.id, id)
    from app.schemas.activity_log import ActivityLogResponse
    return {"timeline": [ActivityLogResponse.model_validate(log) for log in replay_logs]}


@router.get(
    "/{id}/analytics/export",
    status_code=status.HTTP_200_OK
)
def export_analytics_csv(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compiles and downloads workspace metrics aggregated into a CSV report.
    """
    from app.services.permission_service import PermissionService
    PermissionService.check_permission(db, current_user.id, id, "view_workspace")
    import csv
    import io
    from fastapi.responses import StreamingResponse
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Workspace ID", id])
    stats = ConversationService.get_workspace_stats(db, current_user.id, id)
    writer.writerow(["Total Conversations", stats.total_conversations])
    writer.writerow(["Total Messages", stats.total_messages])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=workspace_{id}_analytics.csv"}
    )

