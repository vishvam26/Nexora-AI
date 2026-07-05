from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.user import User


class ConversationComment(Base):
    """
    Model representing user comments/replies inside a conversation thread.
    """
    __tablename__ = "conversation_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversation_comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation")
    user: Mapped["User"] = relationship("User")
    
    parent: Mapped[Optional["ConversationComment"]] = relationship(
        "ConversationComment", remote_side=[id], back_populates="replies"
    )
    replies: Mapped[List["ConversationComment"]] = relationship(
        "ConversationComment", back_populates="parent", cascade="all, delete-orphan"
    )
