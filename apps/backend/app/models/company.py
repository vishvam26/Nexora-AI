from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace
    from app.models.company_settings import CompanySettings
    from app.models.company_secrets import CompanySecrets
    from app.models.invitation import Invitation

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="FREE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    settings: Mapped[Optional["CompanySettings"]] = relationship(
        "CompanySettings", back_populates="company", cascade="all, delete-orphan"
    )
    secrets: Mapped[List["CompanySecrets"]] = relationship(
        "CompanySecrets", back_populates="company", cascade="all, delete-orphan"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="company"
    )
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace", back_populates="company", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["Invitation"]] = relationship(
        "Invitation", back_populates="company", cascade="all, delete-orphan"
    )
