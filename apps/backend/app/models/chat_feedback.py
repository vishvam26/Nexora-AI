from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, DateTime, Boolean, Float, Text

from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g., 1-5 scale rating
    thumbs_up: Mapped[bool] = mapped_column(Boolean, default=False)
    thumbs_down: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Volume 4 Evaluation & Replay Fields
    faithfulness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    answer_relevance: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    context_recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hallucination_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(50), default="LOW")
    query_hash: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Human-in-the-loop Review system
    review_status: Mapped[str] = mapped_column(String(50), default="pending") # pending, approved, rejected
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_flagged_for_tuning: Mapped[bool] = mapped_column(Boolean, default=False)


    # Version Tracking
    model_version: Mapped[Optional[str]] = mapped_column(String(100), default="nexora-v1")
    dataset_version: Mapped[Optional[str]] = mapped_column(String(100), default="ds-v1")
    rag_pipeline_version: Mapped[Optional[str]] = mapped_column(String(100), default="rag-v2.1")

    # Debugging Context & Analytics
    root_cause: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Retrieval Failure, Hallucination, etc
    domain_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # Finance, SQL, HR, etc
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Replay Payload Store
    replay_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replay_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replay_chunks: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Stored as JSON string


