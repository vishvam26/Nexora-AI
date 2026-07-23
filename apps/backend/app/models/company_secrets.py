from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.db.database import Base

if TYPE_CHECKING:
    from app.models.company import Company

class CompanySecrets(Base):
    __tablename__ = "company_secrets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    encrypted_api_key: Mapped[str] = mapped_column(String(512), nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="secrets")
