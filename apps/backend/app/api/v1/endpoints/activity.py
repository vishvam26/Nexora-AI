from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.security.dependencies import get_current_user
from app.services.permission_service import PermissionService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/activity",
    tags=["Workspace Activity Feed"]
)


@router.get("/", status_code=status.HTTP_200_OK)
def get_workspace_activity_feed(
    workspace_id: int,
    limit: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a GitHub-like activity feed/timeline of recent events in the team workspace.
    """
    PermissionService.validate_workspace_access(db, current_user.id, workspace_id)

    logs = db.query(ActivityLog).filter(
        ActivityLog.workspace_id == workspace_id
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()

    feed = []
    for log in logs:
        # Resolve username
        user_name = log.user.full_name if log.user else "System"
        
        # Formulate description based on action and entity
        description = f"{user_name} performed {log.action} on {log.entity}"
        if log.metadata_json and "title" in log.metadata_json:
            description = f"{user_name} {log.action.lower()} '{log.metadata_json['title']}'"
        elif log.metadata_json and "file_name" in log.metadata_json:
            description = f"{user_name} uploaded file '{log.metadata_json['file_name']}'"
            
        feed.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": user_name,
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "description": description,
            "created_at": log.created_at
        })

    return feed
