from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services.ml.ml_service import MLService
from app.schemas.ml import MLTrainRequest, MLPredictRequest

router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"]
)


@router.get(
    "/options/{doc_id}",
    response_model=Dict[str, Any],
    summary="Fetch column names and target recommendations for ML modeling"
)
def get_ml_options(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    data = MLService.get_features_and_targets(doc.storage_path)
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=data["error"]
        )
    return data


@router.post(
    "/train/{doc_id}",
    response_model=Dict[str, Any],
    summary="Train a machine learning model pipeline on selected targets"
)
def train_model(
    doc_id: int,
    payload: MLTrainRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    data = MLService.train_pipeline(
        doc_id=doc_id,
        file_path=doc.storage_path,
        target_col=payload.target_column,
        feature_cols=payload.feature_columns,
        algorithm=payload.algorithm
    )
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=data["error"]
        )
    return data


@router.post(
    "/predict/{doc_id}",
    response_model=Dict[str, Any],
    summary="Run live single row prediction on the trained model"
)
def predict_data(
    doc_id: int,
    payload: MLPredictRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    data = MLService.make_prediction(doc_id=doc_id, inputs=payload.inputs)
    if "error" in data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=data["error"]
        )
    return data
