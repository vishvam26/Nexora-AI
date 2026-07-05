from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, DateTime, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class TrainingProject(Base):
    __tablename__ = "training_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    base_model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Draft", index=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="Queued", index=True)
    lora_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    training_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    current_epoch: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gpu_usage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vram_usage_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TrainingArtifact(Base):
    __tablename__ = "training_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TrainingLog(Base):
    __tablename__ = "training_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("training_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    loss: Mapped[float] = mapped_column(Float, nullable=False)
    learning_rate: Mapped[float] = mapped_column(Float, nullable=False)
    tokens_per_sec: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
