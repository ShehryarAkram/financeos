"""
Journal Service — the accounting engine.

This is the most critical file in the entire project.
Every financial transaction flows through here.
Rule: debits MUST equal credits. Always. No exceptions.
"""

import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.models.journal import JournalEntry, JournalLine, EntrySource
from app.models.account import Account, AccountType, NORMAL_BALANCE_MAP
from app.models.contact import Contact

class JournalError(Exception):
    pass

class JournalService:

    @staticmethod
    def create_entry(
        db: Session,
        org_id: uuid.UUID,
        entry_date: date,
        narration: str,
        lines: list[dict],           # [{"account_id": uuid, "debit": 0, "credit": 500, "contact_id": None}]
        reference: str | None = None,
        narration_ur: str | None = None,
        source: EntrySource = EntrySource.manual,
        created_by_user_id: uuid.UUID | None = None,
        post: bool = True,
    ) -> JournalEntry:
        """
        Create and optionally post a journal entry.
        Validates debit == credit before saving.
        """
        if not lines:
            raise JournalError("Journal entry must have at least 2 lines")

        total_debits = sum(Decimal(str(l.get("debit", 0))) for l in lines)
        total_credits = sum(Decimal(str(l.get("credit", 0))) for l in lines)

        if total_debits != total_credits:
            raise JournalError(
                f"Journal entry does not balance: "
                f"Debits={total_debits}, Credits={total_credits}"
            )

        if total_debits == 0:
            raise JournalError("Journal entry cannot have zero amounts")

        entry = JournalEntry(
            org_id=org_id,
            date=entry_date,
            reference=reference,
            narration=narration,
            narration_ur=narration_ur,
            source=source,
            is_posted=post,
            created_by_user_id=created_by_user_id,
        )
        db.add(entry)
        db.flush()  # get entry.id without committing

        for line_data in lines:
            debit = Decimal(str(line_data.get("debit", 0)))
            credit = Decimal(str(line_data.get("credit", 0)))

            if debit == 0 and credit == 0:
                raise JournalError("Each journal line must have a non-zero amount")

            line = JournalLine(
                entry_id=entry.id,
                account_id=line_data["account_id"],
                debit=debit,
                credit=credit,
                description=line_data.get("description"),
                contact_id=line_data.get("contact_id"),
            )
            db.add(line)

        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def get_account_balance(
        db: Session,
        org_id: uuid.UUID,
        account_id: uuid.UUID,
        as_of: date | None = None,
    ) -> Decimal:
        """
        Returns the balance of an account.
        Positive = normal balance side (debit for assets, credit for liabilities/income).
        """
        query = (
            db.query(
                func.sum(JournalLine.debit).label("total_debit"),
                func.sum(JournalLine.credit).label("total_credit"),
            )
            .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
            .filter(
                JournalEntry.org_id == org_id,
                JournalLine.account_id == account_id,
                JournalEntry.is_posted == True,
            )
        )

        if as_of:
            query = query.filter(JournalEntry.date <= as_of)

        result = query.one()
        total_debit = result.total_debit or Decimal("0")
        total_credit = result.total_credit or Decimal("0")

        account = db.get(Account, account_id)
        if not account:
            raise JournalError(f"Account {account_id} not found")

        # Assets and expenses increase with debits
        from app.models.account import NormalBalance
        if account.normal_balance == NormalBalance.debit:
            return total_debit - total_credit
        else:
            return total_credit - total_debit

    @staticmethod
    def get_trial_balance(db: Session, org_id: uuid.UUID, as_of: date | None = None) -> list[dict]:
        """Returns trial balance — all accounts with their debit/credit balances"""
        accounts = db.query(Account).filter(
            Account.org_id == org_id,
            Account.is_active == True,
        ).order_by(Account.code).all()

        rows = []
        for account in accounts:
            balance = JournalService.get_account_balance(db, org_id, account.id, as_of)
            if balance == 0:
                continue

            from app.models.account import NormalBalance
            debit_bal = balance if account.normal_balance == NormalBalance.debit else Decimal("0")
            credit_bal = balance if account.normal_balance == NormalBalance.credit else Decimal("0")

            rows.append({
                "account_code": account.code,
                "account_name": account.name,
                "account_name_ur": account.name_ur,
                "type": account.type.value,
                "debit": float(debit_bal),
                "credit": float(credit_bal),
            })

        return rows

    @staticmethod
    def get_profit_and_loss(
        db: Session,
        org_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Generate P&L statement for a period"""
        accounts = db.query(Account).filter(
            Account.org_id == org_id,
            Account.type.in_([AccountType.income, AccountType.expense]),
            Account.parent_id != None,  # leaf accounts only
            Account.is_active == True,
        ).order_by(Account.code).all()

        income_lines = []
        expense_lines = []
        total_income = Decimal("0")
        total_expenses = Decimal("0")

        for account in accounts:
            # Balance restricted to date range
            query = (
                db.query(
                    func.sum(JournalLine.debit).label("total_debit"),
                    func.sum(JournalLine.credit).label("total_credit"),
                )
                .join(JournalEntry)
                .filter(
                    JournalEntry.org_id == org_id,
                    JournalLine.account_id == account.id,
                    JournalEntry.is_posted == True,
                    JournalEntry.date >= from_date,
                    JournalEntry.date <= to_date,
                )
            )
            result = query.one()
            debit = result.total_debit or Decimal("0")
            credit = result.total_credit or Decimal("0")

            from app.models.account import NormalBalance
            balance = credit - debit if account.normal_balance == NormalBalance.credit else debit - credit

            if balance == 0:
                continue

            row = {
                "code": account.code,
                "name": account.name,
                "name_ur": account.name_ur,
                "amount": float(balance),
            }

            if account.type == AccountType.income:
                income_lines.append(row)
                total_income += balance
            else:
                expense_lines.append(row)
                total_expenses += balance

        return {
            "period": {"from": str(from_date), "to": str(to_date)},
            "income": income_lines,
            "expenses": expense_lines,
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_profit": float(total_income - total_expenses),
        }

    # ─── Convenience entry creators ──────────────────────────────────────────

    @staticmethod
    def record_cash_sale(
        db: Session,
        org_id: uuid.UUID,
        amount: Decimal,
        cash_account_id: uuid.UUID,
        revenue_account_id: uuid.UUID,
        narration: str = "Cash sale",
        narration_ur: str | None = None,
        entry_date: date | None = None,
        contact_id: uuid.UUID | None = None,
    ) -> JournalEntry:
        """DR Cash / CR Revenue — simplest sale transaction"""
        return JournalService.create_entry(
            db=db,
            org_id=org_id,
            entry_date=entry_date or date.today(),
            narration=narration,
            narration_ur=narration_ur or "نقد فروخت",
            source=EntrySource.whatsapp_bot,
            lines=[
                {"account_id": cash_account_id, "debit": amount, "credit": 0, "contact_id": contact_id},
                {"account_id": revenue_account_id, "debit": 0, "credit": amount},
            ],
        )

    @staticmethod
    def record_udhar_sale(
        db: Session,
        org_id: uuid.UUID,
        amount: Decimal,
        ar_account_id: uuid.UUID,
        revenue_account_id: uuid.UUID,
        contact_id: uuid.UUID,
        narration: str = "Credit sale",
        narration_ur: str | None = None,
        entry_date: date | None = None,
    ) -> JournalEntry:
        """DR Accounts Receivable / CR Revenue — udhar transaction"""
        # Also update contact udhar balance
        contact = db.get(Contact, contact_id)
        if contact:
            contact.udhar_balance = float(Decimal(str(contact.udhar_balance)) + amount)

        entry = JournalService.create_entry(
            db=db,
            org_id=org_id,
            entry_date=entry_date or date.today(),
            narration=narration,
            narration_ur=narration_ur or "ادھار فروخت",
            source=EntrySource.whatsapp_bot,
            lines=[
                {"account_id": ar_account_id, "debit": amount, "credit": 0, "contact_id": contact_id},
                {"account_id": revenue_account_id, "debit": 0, "credit": amount},
            ],
        )
        db.commit()
        return entry

    @staticmethod
    def record_udhar_payment(
        db: Session,
        org_id: uuid.UUID,
        amount: Decimal,
        cash_account_id: uuid.UUID,
        ar_account_id: uuid.UUID,
        contact_id: uuid.UUID,
        narration: str = "Udhar payment received",
        entry_date: date | None = None,
    ) -> JournalEntry:
        """DR Cash / CR AR — customer pays back udhar"""
        contact = db.get(Contact, contact_id)
        if contact:
            contact.udhar_balance = float(Decimal(str(contact.udhar_balance)) - amount)

        entry = JournalService.create_entry(
            db=db,
            org_id=org_id,
            entry_date=entry_date or date.today(),
            narration=narration,
            narration_ur="ادھار وصولی",
            source=EntrySource.whatsapp_bot,
            lines=[
                {"account_id": cash_account_id, "debit": amount, "credit": 0},
                {"account_id": ar_account_id, "debit": 0, "credit": amount, "contact_id": contact_id},
            ],
        )
        db.commit()
        return entry
