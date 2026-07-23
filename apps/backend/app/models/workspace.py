import uuid as uuid_pkg
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.folder import Folder
    from app.models.company import Company


class Workspace(Base):
    """
    Model representing a Workspace which isolates conversations and other assets.
    """
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid_pkg.uuid4()),
        nullable=False
    )
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="💼")
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#4F46E5")
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="private", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)

    # Branding
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    accent_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    theme: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    welcome_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Settings
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    date_format: Mapped[str] = mapped_column(String(20), nullable=False, default="YYYY-MM-DD")
    ai_model_preference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    guest_policy: Mapped[str] = mapped_column(String(20), nullable=False, default="allowed")
    sharing_policy: Mapped[str] = mapped_column(String(20), nullable=False, default="allowed")
    retention_period_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    auto_archive_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    history_size_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Enterprise Policies
    disable_sharing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_exports: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_public_links: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_invite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_downloads: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_comments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_reactions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_domains: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata & Quotas
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    region: Mapped[str] = mapped_column(String(20), nullable=False, default="us")
    data_residency: Mapped[str] = mapped_column(String(20), nullable=False, default="us")
    organization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    license_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=None)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="workspaces")
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="workspaces")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="workspace", cascade="all, delete-orphan"
    )
    folders: Mapped[list["Folder"]] = relationship(
        "Folder", back_populates="workspace", cascade="all, delete-orphan"
    )

