import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.training_project import TrainingProject, TrainingRun, TrainingLog, TrainingArtifact
from app.services.unsloth_integration_service import UnslothIntegrationService

logger = logging.getLogger("app.services.training_project_service")


class TrainingProjectService:
    """
    Service coordinating TrainingProject CRUD and asynchronous pipeline queues.
    """

    @staticmethod
    def create_project(
        db: Session,
        workspace_id: int,
        user_id: int,
        name: str,
        base_model: str
    ) -> TrainingProject:
        project = TrainingProject(
            workspace_id=workspace_id,
            name=name,
            base_model=base_model,
            status="Draft",
            created_by=user_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: int) -> TrainingProject:
        return db.query(TrainingProject).filter(TrainingProject.id == project_id).first()

    @staticmethod
    def list_projects(db: Session, workspace_id: int) -> List[TrainingProject]:
        return db.query(TrainingProject).filter(TrainingProject.workspace_id == workspace_id).all()

    @staticmethod
    def initiate_training_run(
        db: Session,
        project_id: int,
        dataset_id: int,
        lora_config: dict,
        training_config: dict
    ) -> TrainingRun:
        """
        Creates and starts a training run pipeline.
        """
        run = TrainingRun(
            project_id=project_id,
            dataset_project_id=dataset_id,
            status="Queued",
            lora_config=lora_config,
            training_config=training_config,
            current_epoch=0,
            current_step=0
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Trigger mock trainer worker
        UnslothIntegrationService.start_training_run(db, run)

        return run

    @staticmethod
    def get_run_logs(db: Session, run_id: int) -> List[TrainingLog]:
        return db.query(TrainingLog).filter(TrainingLog.run_id == run_id).order_by(TrainingLog.step.asc()).all()

    @staticmethod
    def get_run_artifacts(db: Session, run_id: int) -> List[TrainingArtifact]:
        return db.query(TrainingArtifact).filter(TrainingArtifact.run_id == run_id).all()
