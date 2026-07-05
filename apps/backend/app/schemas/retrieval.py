from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class RetrievalMetrics(BaseModel):
    """Logged metrics from each RAG retrieval pass."""
    latency_ms: float
    retrieved_count: int
    dropped_count: int
    avg_similarity: float
    used_fallback: bool = False

    model_config = {"from_attributes": True}


class RetrievedChunk(BaseModel):
    """A single ranked chunk returned by the retrieval pipeline."""
    chunk_id: int
    document_id: int
    text: str
    score: float
    composite_score: Optional[float] = None
    page: Optional[int] = None
    section: Optional[str] = None
    token_count: int
    doc_filename: Optional[str] = None
    kb_title: Optional[str] = None

    model_config = {"from_attributes": True}


class RAGContext(BaseModel):
    """Full result from the RAG pipeline, ready for prompt injection."""
    formatted_context: str
    chunks_used: List[RetrievedChunk]
    metrics: RetrievalMetrics
    has_knowledge: bool
    graph_context: Optional[str] = ""
    confidence_score: float = 0.0

    model_config = {"from_attributes": True}
