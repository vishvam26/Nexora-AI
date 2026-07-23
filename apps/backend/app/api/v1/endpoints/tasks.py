from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.user import User
from app.models.task import Task
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.security.dependencies import get_current_user
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, WorkspaceProgressResponse
from app.services.permission_service import PermissionService
from app.services.activity_service import ActivityService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/tasks",
    tags=["Workspace Tasks"]
)


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    workspace_id: int,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a new task within a workspace. Enforces EDITOR/ADMIN/OWNER roles.
    """
    PermissionService.check_permission(db, current_user.id, workspace_id, "edit_folder") # Tasks creation matches folder permissions
    
    # Check if assigned user is a member of the workspace
    if payload.assigned_to:
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == payload.assigned_to,
            WorkspaceMember.is_active == True
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user is not a member of this workspace"
            )

    task = Task(
        workspace_id=workspace_id,
        title=payload.title,
        description=payload.description,
        assigned_to=payload.assigned_to,
        created_by=current_user.id,
        status=payload.status,
        due_date=payload.due_date
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Log Activity
    ActivityService.log_activity(
        db=db,
        workspace_id=workspace_id,
        user_id=current_user.id,
        action="Task Created",
        entity="Task",
        entity_id=task.id,
        metadata_json={"title": task.title}
    )

    return _enrich_task_response(db, task)


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    workspace_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, in_progress, completed)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists all tasks inside a workspace. Enforces workspace membership.
    """
    PermissionService.validate_workspace_access(db, current_user.id, workspace_id)
    
    query = db.query(Task).filter(Task.workspace_id == workspace_id)
    if status_filter:
        query = query.filter(Task.status == status_filter)
        
    tasks = query.all()
    return [_enrich_task_response(db, t) for t in tasks]


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    workspace_id: int,
    task_id: int,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates task properties, assignment, or status.
    """
    PermissionService.validate_workspace_access(db, current_user.id, workspace_id)
    
    task = db.query(Task).filter(Task.id == task_id, Task.workspace_id == workspace_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found in this workspace"
        )

    # Assignee validation
    if payload.assigned_to is not None:
        member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == payload.assigned_to,
            WorkspaceMember.is_active == True
        ).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned user is not a member of this workspace"
            )
        task.assigned_to = payload.assigned_to

    # Status changes activity log
    old_status = task.status
    if payload.status:
        task.status = payload.status
        if old_status != payload.status and payload.status == "completed":
            ActivityService.log_activity(
                db=db,
                workspace_id=workspace_id,
                user_id=current_user.id,
                action="Task Completed",
                entity="Task",
                entity_id=task.id,
                metadata_json={"title": task.title}
            )

    if payload.title:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.due_date is not None:
        task.due_date = payload.due_date

    db.commit()
    db.refresh(task)
    return _enrich_task_response(db, task)


@router.get("/ai-pm", response_model=WorkspaceProgressResponse)
def get_ai_pm_recommendation(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches the tasks in the workspace, calculates completion metrics,
    and returns a simulated AI status recommendation.
    """
    PermissionService.validate_workspace_access(db, current_user.id, workspace_id)

    tasks = db.query(Task).filter(Task.workspace_id == workspace_id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed")
    
    completion_percentage = 0.0
    if total_tasks > 0:
        completion_percentage = round((completed_tasks / total_tasks) * 100, 2)

    status_summary = {
        "pending": sum(1 for t in tasks if t.status == "pending"),
        "in_progress": sum(1 for t in tasks if t.status == "in_progress"),
        "completed": completed_tasks,
    }

    # Custom simulated AI response based on completion metrics
    ai_status = "Good job! Project is progressing on track."
    if completion_percentage < 30.0:
        ai_status = "Attention Needed: Low completion rate. Consider dividing tasks or scheduling a team sync."
    elif completion_percentage < 70.0:
        ai_status = "Moderate Progress: Keep up the momentum. Tasks are moving steadily to completion."

    return WorkspaceProgressResponse(
        workspace_id=workspace_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        completion_percentage=completion_percentage,
        status_summary=status_summary,
        estimated_completion_days=max(1, (total_tasks - completed_tasks) * 2),
        ai_status_recommendation=ai_status
    )


def _enrich_task_response(db: Session, task: Task) -> TaskResponse:
    assignee_name = None
    creator_name = None
    
    if task.assigned_to:
        u = db.query(User).filter(User.id == task.assigned_to).first()
        if u:
            assignee_name = u.full_name
            
    c = db.query(User).filter(User.id == task.created_by).first()
    if c:
        creator_name = c.full_name

    res = TaskResponse(
        id=task.id,
        workspace_id=task.workspace_id,
        title=task.title,
        description=task.description,
        assigned_to=task.assigned_to,
        created_by=task.created_by,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
        updated_at=task.updated_at,
        assignee_name=assignee_name,
        creator_name=creator_name
    )
    return res
