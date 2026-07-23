from sqlalchemy import Integer, String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.company import Company

class CompanySettings(Base):
    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    default_llm: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    theme: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    branding: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    max_file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allowed_extensions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="settings")
