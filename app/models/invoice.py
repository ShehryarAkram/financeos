import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Enum, ForeignKey, Text, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    partial = "partial"
    overdue = "overdue"
    void = "void"

class TaxType(str, enum.Enum):
    none = "none"
    sales_tax_17 = "sales_tax_17"
    sales_tax_reduced = "sales_tax_reduced"
    wht_153 = "wht_153"
    wht_236 = "wht_236"

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), index=True)
    invoice_number: Mapped[str] = mapped_column(String(50))
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.draft)
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    paid_date: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="PKR")
    tax_type: Mapped[TaxType] = mapped_column(Enum(TaxType), default=TaxType.none)
    notes: Mapped[str | None] = mapped_column(Text)
    whatsapp_sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    whatsapp_reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reminder_at: Mapped[datetime | None] = mapped_column(DateTime)
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    organization: Mapped["Organization"] = relationship("Organization", back_populates="invoices")
    contact: Mapped["Contact"] = relationship("Contact", back_populates="invoices")
    lines: Mapped[list["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("1.000"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="lines")
