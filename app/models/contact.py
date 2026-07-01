import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Enum, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class ContactType(str, enum.Enum):
    customer = "customer"
    supplier = "supplier"
    both = "both"

class Contact(Base):
    __tablename__ = "contacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    contact_type: Mapped[ContactType] = mapped_column(Enum(ContactType), default=ContactType.customer)
    phone: Mapped[str | None] = mapped_column(String(20), index=True)
    whatsapp: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    ntn: Mapped[str | None] = mapped_column(String(20))
    udhar_balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0)
    custom_reminder_message: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    organization: Mapped["Organization"] = relationship("Organization", back_populates="contacts")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="contact")
