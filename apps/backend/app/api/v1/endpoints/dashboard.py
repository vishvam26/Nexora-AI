from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace Dashboard"]
)


@router.get(
    "/{id}/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK
)
def get_workspace_dashboard(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compiles and returns highly aggregated analytics and metadata dashboard for the workspace.
    Avoids N+1 queries.
    """
    return DashboardService.compile_dashboard(db, current_user.id, id)
