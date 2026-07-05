from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from app.models.activity_log import ActivityLog
from app.repositories.activity_repository import ActivityRepository
from app.services.permission_service import PermissionService


class ActivityService:
    """
    Service layer coordinating Workspace auditable Activity Log creation and retrievals.
    """

    @staticmethod
    def log_activity(
        db: Session,
        workspace_id: int,
        user_id: int,
        action: str,
        entity: str,
        entity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActivityLog:
        """
        Creates and stores an auditable log entry for a workspace event.
        """
        log = ActivityLog(
            workspace_id=workspace_id,
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            metadata_json=metadata
        )
        return ActivityRepository.create(db, log)

    @staticmethod
    def get_activity_logs(
        db: Session,
        user_id: int,
        workspace_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[ActivityLog]:
        """
        Retrieves logs, asserting workspace membership/view permission first.
        """
        # Require view permission on the workspace
        PermissionService.check_permission(db, user_id, workspace_id, "view_workspace")
        return ActivityRepository.get_by_workspace_id(db, workspace_id, limit, offset)
