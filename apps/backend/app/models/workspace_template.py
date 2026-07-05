from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WorkspaceTemplate(Base):
    """
    Model representing workspace templates for structured, pre-configured workspace environments.
    """
    __tablename__ = "workspace_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    configuration: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User")
