from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.conversation import Conversation


class Folder(Base):
    """
    Model representing a folder inside a Workspace to categorize conversations.
    """
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    color: Mapped[str] = mapped_column(String(20), nullable=False, default="Blue")
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="📁")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="folders")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="folder", cascade="all, delete-orphan"
    )
