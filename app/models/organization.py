import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Enum, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class PlanType(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ntn: Mapped[str | None] = mapped_column(String(20))
    strn: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    fiscal_year_start: Mapped[date] = mapped_column(Date, default=date(2024, 7, 1))
    phone: Mapped[str | None] = mapped_column(String(20))
    whatsapp: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    plan: Mapped[PlanType] = mapped_column(Enum(PlanType), default=PlanType.free)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    dukandaar_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    users: Mapped[list["OrganizationUser"]] = relationship("OrganizationUser", back_populates="organization")
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="organization")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="organization")
    journal_entries: Mapped[list["JournalEntry"]] = relationship("JournalEntry", back_populates="organization")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="organization")
