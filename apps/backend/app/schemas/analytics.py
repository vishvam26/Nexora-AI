from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class DocumentFrequency(BaseModel):
    document_id: int
    filename: str
    hit_count: int


class RetrievalDashboardMetrics(BaseModel):
    average_latency_ms: float
    average_confidence: float
    total_queries: int
    intent_distribution: Dict[str, int]
    top_documents: List[DocumentFrequency]


class RAGDebugBreakdown(BaseModel):
    query: str
    intent: str
    strategy: str
    confidence_score: float
    latency_ms: float
    chunks_retrieved: int
    chunks_accepted: int
    chunks_rejected: int
    raw_context_size_chars: int
    token_estimate: int
