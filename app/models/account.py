import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Enum, ForeignKey, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class AccountType(str, enum.Enum):
    asset = "asset"
    liability = "liability"
    equity = "equity"
    income = "income"
    expense = "expense"

class NormalBalance(str, enum.Enum):
    debit = "debit"
    credit = "credit"

# Normal balance rules (fundamental accounting):
# Assets = Debit | Liabilities = Credit | Equity = Credit
# Income = Credit | Expenses = Debit
NORMAL_BALANCE_MAP = {
    AccountType.asset: NormalBalance.debit,
    AccountType.liability: NormalBalance.credit,
    AccountType.equity: NormalBalance.credit,
    AccountType.income: NormalBalance.credit,
    AccountType.expense: NormalBalance.debit,
}

class Account(Base):
    """Chart of Accounts — the skeleton of the entire financial system"""
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    code: Mapped[str] = mapped_column(String(20))       # 1001, 2001, 4001 etc.
    name: Mapped[str] = mapped_column(String(255))      # "Cash", "Accounts Receivable"
    name_ur: Mapped[str | None] = mapped_column(String(255))  # Urdu name: "نقد", "وصولی"

    type: Mapped[AccountType] = mapped_column(Enum(AccountType))
    normal_balance: Mapped[NormalBalance] = mapped_column(Enum(NormalBalance))

    # Sub-account support (e.g. Bank → HBL Account, MCB Account)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))

    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # system accounts can't be deleted

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="accounts")
    journal_lines: Mapped[list["JournalLine"]] = relationship("JournalLine", back_populates="account")
    children: Mapped[list["Account"]] = relationship("Account", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Account {self.code} {self.name}>"


# ── Pakistan Default COA ──────────────────────────────────────────────────────
# Call seed_default_accounts(org_id, db) after creating a new organization

PAKISTAN_DEFAULT_COA = [
    # ASSETS (1xxx)
    ("1000", "Current Assets",         "موجودہ اثاثے",     AccountType.asset,   None),
    ("1001", "Cash in Hand",           "ہاتھ میں نقد",      AccountType.asset,   "1000"),
    ("1002", "Cash at Bank",           "بینک میں رقم",      AccountType.asset,   "1000"),
    ("1003", "Accounts Receivable",    "واجب الوصول",       AccountType.asset,   "1000"),
    ("1004", "Inventory / Stock",      "مال",               AccountType.asset,   "1000"),
    ("1005", "Advance Payments",       "پیشگی ادائیگی",     AccountType.asset,   "1000"),
    ("1100", "Fixed Assets",           "مستقل اثاثے",       AccountType.asset,   None),
    ("1101", "Furniture & Equipment",  "فرنیچر و سامان",    AccountType.asset,   "1100"),
    ("1102", "Vehicles",               "گاڑیاں",            AccountType.asset,   "1100"),

    # LIABILITIES (2xxx)
    ("2000", "Current Liabilities",   "موجودہ واجبات",      AccountType.liability, None),
    ("2001", "Accounts Payable",      "واجب الادا",         AccountType.liability, "2000"),
    ("2002", "Sales Tax Payable",     "سیلز ٹیکس واجب",    AccountType.liability, "2000"),
    ("2003", "WHT Payable",           "ود ہولڈنگ ٹیکس",    AccountType.liability, "2000"),
    ("2004", "Salaries Payable",      "تنخواہیں واجب",      AccountType.liability, "2000"),
    ("2005", "Loans Payable",         "قرض واجب",           AccountType.liability, "2000"),

    # EQUITY (3xxx)
    ("3000", "Owner's Equity",        "مالک کا حصہ",        AccountType.equity, None),
    ("3001", "Capital",               "سرمایہ",             AccountType.equity, "3000"),
    ("3002", "Drawings",              "نکاسی",              AccountType.equity, "3000"),
    ("3003", "Retained Earnings",     "محفوظ آمدنی",        AccountType.equity, "3000"),

    # INCOME (4xxx)
    ("4000", "Revenue",               "آمدن",               AccountType.income, None),
    ("4001", "Sales Revenue",         "فروخت آمدن",         AccountType.income, "4000"),
    ("4002", "Service Revenue",       "خدمت آمدن",          AccountType.income, "4000"),
    ("4003", "Other Income",          "دیگر آمدن",          AccountType.income, "4000"),

    # EXPENSES (5xxx)
    ("5000", "Cost of Goods Sold",    "مال کی لاگت",        AccountType.expense, None),
    ("5001", "Purchase",              "خریداری",             AccountType.expense, "5000"),
    ("5100", "Operating Expenses",    "کاروباری اخراجات",   AccountType.expense, None),
    ("5101", "Rent",                  "کرایہ",              AccountType.expense, "5100"),
    ("5102", "Utilities",             "بجلی/گیس/پانی",      AccountType.expense, "5100"),
    ("5103", "Salaries Expense",      "تنخواہیں",           AccountType.expense, "5100"),
    ("5104", "Mobile/Internet",       "موبائل/انٹرنیٹ",     AccountType.expense, "5100"),
    ("5105", "Transport",             "ٹرانسپورٹ",          AccountType.expense, "5100"),
    ("5106", "Miscellaneous",         "متفرق اخراجات",      AccountType.expense, "5100"),
]
