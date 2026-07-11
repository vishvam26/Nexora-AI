"""
Pydantic Schemas for Evaluation & Replay API — Volume 4
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class FeedbackSubmitRequest(BaseModel):
    message_id: int = Field(
        ...,
        description="The ID of the target chat message to evaluate",
    )
    thumbs_up: bool = Field(
        default=False,
        description="True if positive thumbs rating",
    )
    thumbs_down: bool = Field(
        default=False,
        description="True if negative thumbs rating",
    )
    feedback_text: Optional[str] = Field(
        default=None,
        description="Optional textual explanation comment",
        max_length=500,
    )
    # Debugging logs & metadata
    response_time_ms: Optional[int] = Field(
        default=None,
        description="Response latency time in milliseconds",
    )
    # Replay capture payloads passed from client state memory
    original_query: str = Field(
        ...,
        description="The original user query text",
    )
    context_chunks: List[str] = Field(
        default_factory=list,
        description="Context document chunks retrieved during chat generation",
    )
    prompt_text: Optional[str] = Field(
        default=None,
        description="The constructed RAG prompt",
    )


class EvalMetricsSummary(BaseModel):
    avg_faithfulness: float
    avg_relevance: float
    avg_recall: float
    avg_hallucination: float
    avg_confidence: float
    avg_latency_ms: float
    satisfaction_rate: float
    positive_feedback_count: int
    negative_feedback_count: int
    pending_reviews_count: int
    approved_samples_count: int
    rejected_samples_count: int
    dataset_size_bytes: int
    current_model_version: str


class TuningCandidateResponse(BaseModel):
    id: int
    query: Optional[str] = "Unknown Query"
    original_response: Optional[str] = "No Response Content"
    faithfulness: Optional[float] = 0.0
    hallucination_score: Optional[float] = 0.0
    confidence_score: Optional[float] = 0.0
    priority: Optional[str] = "LOW"
    review_status: Optional[str] = "pending"
    root_cause: Optional[str] = None
    domain_tag: Optional[str] = None
    model_version: Optional[str] = "nexora-v1"
    rag_pipeline_version: Optional[str] = "rag-v2.1"
    created_at: Optional[str] = ""
