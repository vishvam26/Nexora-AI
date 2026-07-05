from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.workspace_import_service import WorkspaceImportService

router = APIRouter(
    prefix="/workspaces",
    tags=["Workspace Import & Export"]
)


@router.post(
    "/{id}/import",
    status_code=status.HTTP_200_OK
)
def import_workspace_data(
    id: int,
    file: UploadFile = File(..., description="Upload .zip, .json, .md, or .txt file containing conversation exports"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enterprise Import Engine: Restores or populates folders and conversation trees from JSON, Markdown, ChatGPT or ZIP structures.
    """
    return WorkspaceImportService.import_from_file(
        db=db,
        user_id=current_user.id,
        workspace_id=id,
        file=file
    )
