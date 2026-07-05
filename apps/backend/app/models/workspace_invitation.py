import uuid as uuid_pkg
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.user import User


class WorkspaceInvitation(Base):
    """
    Model representing user invitations sent to join a Workspace.
    """
    __tablename__ = "workspace_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workspace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    invited_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="VIEWER")
    token: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid_pkg.uuid4()),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace")
    inviter: Mapped["User"] = relationship("User")
