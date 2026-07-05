from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.message import Message
    from app.models.workspace import Workspace
    from app.models.folder import Folder


class Conversation(Base):
    """
    Model representing a chat conversation belonging to a User.
    """
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True
    )
    folder_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    share_token: Mapped[Optional[str]] = mapped_column(String(36), unique=True, nullable=True, index=True)
    share_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    workspace: Mapped[Optional["Workspace"]] = relationship("Workspace", back_populates="conversations")
    folder: Mapped[Optional["Folder"]] = relationship("Folder", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )



