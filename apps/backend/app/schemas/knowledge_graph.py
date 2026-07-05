from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class KnowledgeNodeResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    entity_type: str
    document_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeEdgeResponse(BaseModel):
    id: int
    workspace_id: int
    source_node_id: int
    target_node_id: int
    relation_type: str
    weight: float
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeGraphData(BaseModel):
    nodes: List[KnowledgeNodeResponse]
    edges: List[KnowledgeEdgeResponse]


class RetrievalLogResponse(BaseModel):
    id: int
    workspace_id: int
    query: str
    intent: str
    latency_ms: float
    confidence_score: float
    chunks_retrieved: int
    chunks_accepted: int
    chunks_rejected: int
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryExpansionRequest(BaseModel):
    query: str


class QueryExpansionResponse(BaseModel):
    original_query: str
    expanded_terms: List[str]


class QueryAnalysisRequest(BaseModel):
    query: str


class QueryAnalysisResponse(BaseModel):
    query: str
    intent: str
    extracted_keywords: List[str]
