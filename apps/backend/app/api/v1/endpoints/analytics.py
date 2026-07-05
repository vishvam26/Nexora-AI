from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services.analytics.analytics_engine import AnalyticsEngine
from app.services.analytics.insight_engine import AIInsightEngine
from app.schemas.analytics import ChartDataRequest, InsightRequest

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get(
    "/profile/{doc_id}",
    response_model=Dict[str, Any],
    summary="Generate or fetch descriptive stats and quality EDA data profile for spreadsheet"
)
def get_dataset_profile(
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
    # Check access permission if needed
    profile = AnalyticsEngine.get_profile(doc_id, doc.storage_path)
    if "error" in profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=profile["error"]
        )
    return profile


@router.post(
    "/chart/{doc_id}",
    response_model=List[Dict[str, Any]],
    summary="Fetch aggregated chart group elements coordinate list"
)
def get_chart_aggregates(
    doc_id: int,
    payload: ChartDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    data = AnalyticsEngine.get_aggregated_chart(
        file_path=doc.storage_path,
        x_col=payload.x_column,
        y_col=payload.y_column,
        aggregation=payload.aggregation
    )
    return data


@router.post(
    "/insights/{doc_id}",
    response_model=Dict[str, Any],
    summary="Get LLM statistical business insights of the dataset"
)
def get_ai_insights(
    doc_id: int,
    payload: InsightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = KnowledgeDocumentRepository.get_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    profile = AnalyticsEngine.get_profile(doc_id, doc.storage_path)
    insights = AIInsightEngine.generate_insights(profile, focus_query=payload.query)
    return {"insights": insights}
