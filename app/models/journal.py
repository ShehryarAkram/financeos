import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Boolean, Enum, ForeignKey, Text, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class EntrySource(str, enum.Enum):
    manual = "manual"           # entered via Business Mode UI
    whatsapp_bot = "whatsapp_bot"  # created by WhatsApp bot message
    invoice = "invoice"         # auto-created when invoice is posted
    expense = "expense"         # auto-created from expense entry
    bank_import = "bank_import" # imported from bank CSV
    ai_categorized = "ai_categorized"  # AI auto-categorized

class JournalEntry(Base):
    """
    The heart of the system — every financial transaction is a journal entry.
    Golden rule: sum(debits) == sum(credits) always. Enforced in the service layer.
    """
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reference: Mapped[str | None] = mapped_column(String(100))      # INV-001, CHQ-042, etc.
    narration: Mapped[str] = mapped_column(Text)                     # human-readable description
    narration_ur: Mapped[str | None] = mapped_column(Text)          # Urdu description

    source: Mapped[EntrySource] = mapped_column(Enum(EntrySource), default=EntrySource.manual)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=True)   # False = draft
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Created by
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="journal_entries")
    lines: Mapped[list["JournalLine"]] = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JournalEntry {self.reference} {self.date}>"


class JournalLine(Base):
    """Each debit or credit line within a journal entry"""
    __tablename__ = "journal_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), index=True)

    debit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    description: Mapped[str | None] = mapped_column(Text)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"))  # for AR/AP tracking

    # DB constraint: a line must have either debit OR credit, not both, not neither
    __table_args__ = (
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)",
            name="ck_journal_lines_debit_or_credit"
        ),
    )

    # Relationships
    entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines")
