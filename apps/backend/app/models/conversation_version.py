from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, Text, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.user import User


class ConversationVersion(Base):
    """
    Model representing historical message edits and revisions inside a conversation.
    """
    __tablename__ = "conversation_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    before_content: Mapped[str] = mapped_column(Text, nullable=False)
    after_content: Mapped[str] = mapped_column(Text, nullable=False)
    editor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation")
    editor: Mapped["User"] = relationship("User")
