from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.conversation_comment import ConversationComment
    from app.models.user import User


class Mention(Base):
    """
    Model representing user mentions inside conversation comments.
    """
    __tablename__ = "mentions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversation_comments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mentioned_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    comment: Mapped["ConversationComment"] = relationship("ConversationComment")
    mentioned_user: Mapped["User"] = relationship("User")
