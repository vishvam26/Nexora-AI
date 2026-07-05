import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.models.knowledge_graph import KnowledgeNode, KnowledgeEdge
from app.models.retrieval_log import RetrievalLog
from app.schemas.knowledge_graph import (
    KnowledgeNodeResponse,
    KnowledgeGraphData,
    RetrievalLogResponse,
    QueryExpansionRequest,
    QueryExpansionResponse,
    QueryAnalysisRequest,
    QueryAnalysisResponse
)
from app.schemas.retrieval import RAGContext
from app.services.rag_service import RAGService
from app.services.intent_service import IntentService
from app.services.hybrid_search_service import HybridSearchService

logger = logging.getLogger("app.api.advanced_search")

router = APIRouter(prefix="/search", tags=["Hybrid Search & Graph Intelligence"])


@router.get(
    "/hybrid",
    response_model=RAGContext,
    summary="Perform Advanced Hybrid Search + Knowledge Graph context retrieval"
)
def retrieve_hybrid_context(
    query: str = Query(..., description="The query to search"),
    workspace_id: int = Query(..., description="Workspace ID to isolate search scope"),
    kb_id: Optional[int] = Query(None, description="Optional Knowledge Base ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes intent detection, query expansion, vector & BM25 keyword search,
    knowledge graph traversing, multi-factor reranking, and returns structured RAG Context.
    """
    from app.config import settings
    return RAGService.retrieve_context(
        db=db,
        user_query=query,
        workspace_id=workspace_id,
        knowledge_base_id=kb_id,
        top_k=settings.RAG_TOP_K,
        similarity_threshold=settings.SIMILARITY_THRESHOLD,
        max_context_tokens=settings.MAX_CONTEXT_TOKENS,
        enable_reranking=settings.ENABLE_RERANKING,
        vector_weight=settings.HYBRID_VECTOR_WEIGHT,
        keyword_weight=settings.HYBRID_KEYWORD_WEIGHT,
        graph_max_depth=settings.GRAPH_MAX_DEPTH
    )


@router.get(
    "/graph",
    response_model=KnowledgeGraphData,
    summary="Get full Knowledge Graph nodes and connections"
)
def get_knowledge_graph(
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns nodes and connecting edges belonging to this workspace."""
    nodes = db.query(KnowledgeNode).filter(KnowledgeNode.workspace_id == workspace_id).all()
    edges = db.query(KnowledgeEdge).filter(KnowledgeEdge.workspace_id == workspace_id).all()
    return KnowledgeGraphData(nodes=nodes, edges=edges)


@router.get(
    "/node/{id}",
    response_model=KnowledgeNodeResponse,
    summary="Get single Knowledge Graph Node details"
)
def get_node(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    node = db.query(KnowledgeNode).filter(KnowledgeNode.id == id).first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph Node not found")
    return node


@router.get(
    "/analytics/retrieval",
    response_model=List[RetrievalLogResponse],
    summary="Get recent Retrieval Logs and Analytics"
)
def get_retrieval_logs(
    workspace_id: int = Query(..., description="Workspace ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns recent log entries tracking latencies, confidence metrics, and hit metrics."""
    return (
        db.query(RetrievalLog)
        .filter(RetrievalLog.workspace_id == workspace_id)
        .order_by(RetrievalLog.created_at.desc())
        .limit(50)
        .all()
    )


@router.post(
    "/query/expand",
    response_model=QueryExpansionResponse,
    summary="Expand search query synonyms"
)
def expand_query(
    schema: QueryExpansionRequest,
    current_user: User = Depends(get_current_user),
):
    expanded = IntentService.expand_query(schema.query)
    return QueryExpansionResponse(original_query=schema.query, expanded_terms=expanded)


@router.post(
    "/query/analyze",
    response_model=QueryAnalysisResponse,
    summary="Analyze query intent and extract token keywords"
)
def analyze_query(
    schema: QueryAnalysisRequest,
    current_user: User = Depends(get_current_user),
):
    intent = IntentService.detect_intent(schema.query)
    from app.services.query_service import QueryService
    keywords = QueryService.extract_keywords(schema.query)
    return QueryAnalysisResponse(query=schema.query, intent=intent, extracted_keywords=keywords)
