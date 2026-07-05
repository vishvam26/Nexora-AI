import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.dataset_project import DatasetProject, DatasetVersion, DatasetReviewItem
from app.services.dataset_collector_service import DatasetCollectorService
from app.services.dataset_export_service import DatasetExportService
from app.services.dataset_validation_service import DatasetValidationService
from app.services.pii_masking_service import PIIMaskingService
from app.services.dataset_cleaning_service import DatasetCleaningService

logger = logging.getLogger("app.services.dataset_project_service")


class DatasetProjectService:
    """
    Service coordinating DatasetProject lifecycle, cleaning pipelines, versioning,
    reviews, validations, and exports.
    """

    @staticmethod
    def create_project(
        db: Session,
        workspace_id: int,
        user_id: int,
        name: str,
        description: str = None,
        language: str = "English",
        visibility: str = "private"
    ) -> DatasetProject:
        """Creates a new Dataset project."""
        project = DatasetProject(
            workspace_id=workspace_id,
            name=name,
            description=description,
            language=language,
            visibility=visibility,
            created_by=user_id,
            status="Draft"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: int) -> DatasetProject:
        return db.query(DatasetProject).filter(DatasetProject.id == project_id).first()

    @staticmethod
    def list_projects(db: Session, workspace_id: int) -> List[DatasetProject]:
        return db.query(DatasetProject).filter(DatasetProject.workspace_id == workspace_id).all()

    @staticmethod
    def run_cleaning_and_masking(messages: list) -> list:
        """
        Runs text cleaning and PII masking pipeline across message arrays.
        """
        processed = []
        for m in messages:
            if DatasetCleaningService.is_spam_or_invalid(m.content):
                continue
            cleaned = DatasetCleaningService.clean_text(m.content)
            masked = PIIMaskingService.mask_pii(cleaned)

            # Create transient memory copies to avoid updating actual database logs
            from unittest.mock import MagicMock
            msg_mock = MagicMock()
            msg_mock.role = m.role
            msg_mock.content = masked
            processed.append(msg_mock)

        return processed

    @staticmethod
    def create_version_snapshot(
        db: Session,
        project_id: int,
        version_tag: str,
        sample_count: int,
        token_count: int,
        storage_path: str
    ) -> DatasetVersion:
        """Creates immutable version records."""
        version = DatasetVersion(
            project_id=project_id,
            version_tag=version_tag,
            sample_count=sample_count,
            token_count=token_count,
            storage_path=storage_path
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def get_versions(db: Session, project_id: int) -> List[DatasetVersion]:
        return db.query(DatasetVersion).filter(DatasetVersion.project_id == project_id).all()
