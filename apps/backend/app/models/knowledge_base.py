import uuid as uuid_pkg
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User
    from app.models.knowledge_document import KnowledgeDocument


class KnowledgeBase(Base):
    """
    Model representing a RAG Knowledge Base owned by a Workspace.
    """
    __tablename__ = "knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid_pkg.uuid4()),
        nullable=False
    )
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="📚")
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#10B981")
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private", index=True)
    
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    creator: Mapped["User"] = relationship("User")
    documents: Mapped[List["KnowledgeDocument"]] = relationship(
        "KnowledgeDocument", back_populates="knowledge_base", cascade="all, delete-orphan"
    )
