from sqlalchemy.orm import Session
from typing import List
from app.models.activity_log import ActivityLog


class ActivityRepository:
    """
    Repository for handling database logs of activity auditing.
    """

    @staticmethod
    def create(db: Session, log: ActivityLog) -> ActivityLog:
        """
        Saves a new ActivityLog entry.
        """
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_workspace_id(
        db: Session, workspace_id: int, limit: int = 20, offset: int = 0
    ) -> List[ActivityLog]:
        """
        Retrieves paginated logs for a workspace sorted by created_at descending.
        """
        return db.query(ActivityLog).filter(
            ActivityLog.workspace_id == workspace_id
        ).order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()
