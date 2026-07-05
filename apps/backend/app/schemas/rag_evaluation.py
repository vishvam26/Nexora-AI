from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatFeedbackCreate(BaseModel):
    conversation_id: int
    message_id: int
    rating: Optional[int] = Field(None, ge=1, le=5)
    thumbs_up: bool = False
    thumbs_down: bool = False
    feedback: Optional[str] = None


class ChatFeedbackResponse(BaseModel):
    id: int
    user_id: int
    conversation_id: int
    message_id: int
    rating: Optional[int]
    thumbs_up: bool
    thumbs_down: bool
    feedback: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackAnalyticsResponse(BaseModel):
    thumbs_up: int
    thumbs_down: int
    total_reviews: int


class RAGQualityMetrics(BaseModel):
    average_confidence: float
    average_latency_ms: float
    hallucination_rate: float
    feedback_score: float
    cache_hit_ratio: float


class CostEstimateResponse(BaseModel):
    prompt_cost: float
    completion_cost: float
    embedding_cost: float
    total_cost: float
    tokens: Dict[str, int]


class BenchmarkLeaderboardItem(BaseModel):
    strategy: str
    latency_ms: float
    relevance: float
    groundedness: float
    hits_count: int


class BenchmarkResponse(BaseModel):
    query: str
    workspace_id: int
    leaderboard: List[BenchmarkLeaderboardItem]


class SessionReplayResponse(BaseModel):
    message_id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    rag_trace: Dict[str, Any]


class DatasetExportResponse(BaseModel):
    format: str
    total_records: int
    data: List[Dict[str, Any]]
