import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, ForeignKey, Numeric, Text, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class ExpenseCategory(str, enum.Enum):
    rent = "rent"
    utilities = "utilities"
    salaries = "salaries"
    transport = "transport"
    mobile = "mobile"
    office = "office"
    marketing = "marketing"
    maintenance = "maintenance"
    raw_material = "raw_material"
    miscellaneous = "miscellaneous"

CATEGORY_ACCOUNT_MAP = {
    ExpenseCategory.rent:         "5101",
    ExpenseCategory.utilities:    "5102",
    ExpenseCategory.salaries:     "5103",
    ExpenseCategory.mobile:       "5104",
    ExpenseCategory.transport:    "5105",
    ExpenseCategory.miscellaneous:"5106",
    ExpenseCategory.office:       "5106",
    ExpenseCategory.marketing:    "5106",
    ExpenseCategory.maintenance:  "5106",
    ExpenseCategory.raw_material: "5001",
}

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    description: Mapped[str] = mapped_column(String(255))
    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory), default=ExpenseCategory.miscellaneous)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    vendor: Mapped[str | None] = mapped_column(String(255))
    receipt_url: Mapped[str | None] = mapped_column(Text)   # uploaded receipt photo URL
    notes: Mapped[str | None] = mapped_column(Text)

    paid_from: Mapped[str] = mapped_column(String(10), default="cash")  # cash | bank
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
