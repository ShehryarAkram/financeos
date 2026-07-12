"""
Bank Import Router
- Upload CSV → parse → preview transactions
- Confirm import → create journal entries
- Auto-categorize using keywords
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.account import Account
from app.models.journal import EntrySource
from app.services.journal_service import JournalService
from app.services.bank_import_service import parse_bank_csv

router = APIRouter()

CATEGORY_ACCOUNT_MAP = {
    "salary":      "5103",
    "utilities":   "5102",
    "mobile":      "5104",
    "rent":        "5101",
    "transport":   "5105",
    "tax":         "2003",
    "bank_charge": "5106",
    "transfer":    "1002",
    "miscellaneous": "5106",
}


@router.post("/parse")
async def parse_statement(
    file: UploadFile = File(...),
    org_id: str = Form(...),
):
    """Upload bank CSV and get preview of parsed transactions"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(400, "File too large. Max 5MB.")

    try:
        transactions = parse_bank_csv(content, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    total_debits = sum(t["debit"] for t in transactions)
    total_credits = sum(t["credit"] for t in transactions)

    return {
        "transactions": transactions,
        "count": len(transactions),
        "total_debits": total_debits,
        "total_credits": total_credits,
        "message": f"Found {len(transactions)} transactions. Review and confirm to import."
    }


class ImportConfirmRequest(BaseModel):
    org_id: str
    transactions: list[dict]
    bank_account_code: str = "1002"  # default: Cash at Bank


@router.post("/confirm")
def confirm_import(payload: ImportConfirmRequest, db: Session = Depends(get_db)):
    """
    Import confirmed transactions as journal entries.
    Debits (withdrawals) → expense accounts
    Credits (deposits) → income/transfer accounts
    """
    org_id = uuid.UUID(payload.org_id)
    bank_account = db.query(Account).filter(
        Account.org_id == org_id,
        Account.code == payload.bank_account_code,
    ).first()

    if not bank_account:
        raise HTTPException(400, "Bank account not found in chart of accounts")

    imported = 0
    skipped = 0

    for txn in payload.transactions:
        if not txn.get("import", True):  # skip if user unchecked
            skipped += 1
            continue

        try:
            txn_date = date.fromisoformat(txn["date"])
            debit = Decimal(str(txn.get("debit", 0)))
            credit = Decimal(str(txn.get("credit", 0)))
            description = txn.get("description", "Bank transaction")
            category = txn.get("category", "miscellaneous")

            if debit > 0:
                # Withdrawal — money left bank → expense
                exp_code = CATEGORY_ACCOUNT_MAP.get(category, "5106")
                exp_account = db.query(Account).filter(
                    Account.org_id == org_id, Account.code == exp_code
                ).first()
                if exp_account:
                    JournalService.create_entry(
                        db=db, org_id=org_id,
                        entry_date=txn_date,
                        narration=description,
                        source=EntrySource.bank_import,
                        lines=[
                            {"account_id": exp_account.id, "debit": debit, "credit": 0},
                            {"account_id": bank_account.id, "debit": 0, "credit": debit},
                        ],
                    )
                    imported += 1

            elif credit > 0:
                # Deposit — money came into bank → income
                income_account = db.query(Account).filter(
                    Account.org_id == org_id, Account.code == "4001"
                ).first()
                if income_account:
                    JournalService.create_entry(
                        db=db, org_id=org_id,
                        entry_date=txn_date,
                        narration=description,
                        source=EntrySource.bank_import,
                        lines=[
                            {"account_id": bank_account.id, "debit": credit, "credit": 0},
                            {"account_id": income_account.id, "debit": 0, "credit": credit},
                        ],
                    )
                    imported += 1

        except Exception as e:
            print(f"Skipped transaction: {e}")
            skipped += 1
            continue

    return {
        "status": "imported",
        "imported": imported,
        "skipped": skipped,
        "message": f"{imported} transactions imported as journal entries."
    }
