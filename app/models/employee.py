import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Boolean, ForeignKey, Numeric, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class EmployeeStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    terminated = "terminated"

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255))
    cnic: Mapped[str | None] = mapped_column(String(15))          # 42101-1234567-1
    phone: Mapped[str | None] = mapped_column(String(20))
    department: Mapped[str | None] = mapped_column(String(100))
    designation: Mapped[str | None] = mapped_column(String(100))

    basic_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    join_date: Mapped[date] = mapped_column(Date, default=date.today)

    # Deductions
    eobi_employee: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("370.00"))
    eobi_employer: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("1470.00"))

    bank_name: Mapped[str | None] = mapped_column(String(100))
    bank_account: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[EmployeeStatus] = mapped_column(Enum(EmployeeStatus), default=EmployeeStatus.active)
    notes: Mapped[str | None] = mapped_column(Text)

    # Advance salary tracking
    advance_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payslips: Mapped[list["Payslip"]] = relationship("Payslip", back_populates="employee")


class Payslip(Base):
    __tablename__ = "payslips"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)

    year: Mapped[int] = mapped_column()
    month: Mapped[int] = mapped_column()

    basic_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    allowances: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    eobi_deduction: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("370.00"))
    income_tax: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    other_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    net_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2))

    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_date: Mapped[date | None] = mapped_column(Date)
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="payslips")

class AdvanceSalary(Base):
    """Track advance salary given to employees"""
    __tablename__ = "advance_salary"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    date: Mapped[date] = mapped_column(Date, default=date.today)
    reason: Mapped[str | None] = mapped_column(String(255))
    is_recovered: Mapped[bool] = mapped_column(Boolean, default=False)
    recovered_month: Mapped[str | None] = mapped_column(String(7))  # "2026-07"

    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
