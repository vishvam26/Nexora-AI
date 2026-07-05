from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.user import User


class MessageReaction(Base):
    """
    Model representing user emoji reactions to individual messages.
    """
    __tablename__ = "message_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emoji: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    message: Mapped["Message"] = relationship("Message")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_user_reaction"),
    )
