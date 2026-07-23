from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class RetrievalLog(Base):
    """
    Model representing historical vector/semantic search logs.
    Captures search queries, query execution latency, parameters, and returned document sets.
    """
    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    intent: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    chunks_retrieved: Mapped[int] = mapped_column(Integer, nullable=False)
    chunks_accepted: Mapped[int] = mapped_column(Integer, nullable=False)
    chunks_rejected: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
