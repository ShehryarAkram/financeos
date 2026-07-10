from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import date
import uuid

from app.core.database import get_db
from app.models.expense import Expense, ExpenseCategory, CATEGORY_ACCOUNT_MAP
from app.models.account import Account
from app.models.journal import EntrySource
from app.services.journal_service import JournalService

router = APIRouter()


class ExpenseCreate(BaseModel):
    org_id: str
    date: Optional[str] = None
    description: str
    category: str = "miscellaneous"
    amount: float
    vendor: Optional[str] = None
    notes: Optional[str] = None
    paid_from: str = "cash"


def exp_to_dict(e: Expense) -> dict:
    return {
        "id": str(e.id),
        "date": str(e.date),
        "description": e.description,
        "category": e.category.value,
        "amount": float(e.amount),
        "vendor": e.vendor,
        "notes": e.notes,
        "paid_from": e.paid_from,
        "receipt_url": e.receipt_url,
    }


@router.get("/list")
def list_expenses(
    org_id: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Expense).filter(Expense.org_id == uuid.UUID(org_id))
    if from_date:
        query = query.filter(Expense.date >= date.fromisoformat(from_date))
    if to_date:
        query = query.filter(Expense.date <= date.fromisoformat(to_date))
    if category:
        query = query.filter(Expense.category == ExpenseCategory(category))

    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(float(e.amount) for e in expenses)
    return {"expenses": [exp_to_dict(e) for e in expenses], "total": total}


@router.post("/create")
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    org_id = uuid.UUID(payload.org_id)
    category = ExpenseCategory(payload.category)
    amount = Decimal(str(payload.amount))
    exp_date = date.fromisoformat(payload.date) if payload.date else date.today()

    # Get expense account from category map
    account_code = CATEGORY_ACCOUNT_MAP.get(category, "5106")
    exp_account = db.query(Account).filter(
        Account.org_id == org_id, Account.code == account_code
    ).first()

    # Get payment account (cash or bank)
    payment_code = "1001" if payload.paid_from == "cash" else "1002"
    payment_account = db.query(Account).filter(
        Account.org_id == org_id, Account.code == payment_code
    ).first()

    expense = Expense(
        org_id=org_id,
        date=exp_date,
        description=payload.description,
        category=category,
        amount=amount,
        vendor=payload.vendor or None,
        notes=payload.notes or None,
        paid_from=payload.paid_from,
    )
    db.add(expense)
    db.flush()

    # Auto-create journal entry
    if exp_account and payment_account:
        entry = JournalService.create_entry(
            db=db,
            org_id=org_id,
            entry_date=exp_date,
            narration=payload.description,
            source=EntrySource.expense,
            lines=[
                {"account_id": exp_account.id, "debit": amount, "credit": 0},
                {"account_id": payment_account.id, "debit": 0, "credit": amount},
            ],
        )
        expense.journal_entry_id = entry.id

    db.commit()
    db.refresh(expense)
    return exp_to_dict(expense)


@router.delete("/{expense_id}")
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    expense = db.get(Expense, uuid.UUID(expense_id))
    if not expense:
        raise HTTPException(404, "Expense not found")
    db.delete(expense)
    db.commit()
    return {"status": "deleted"}


@router.get("/summary/{org_id}")
def expense_summary(org_id: str, year: int, month: int, db: Session = Depends(get_db)):
    """Monthly expense breakdown by category"""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    from_date = date(year, month, 1)
    to_date = date(year, month, last_day)

    rows = db.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.org_id == uuid.UUID(org_id),
        Expense.date >= from_date,
        Expense.date <= to_date,
    ).group_by(Expense.category).all()

    breakdown = [{"category": r.category.value, "total": float(r.total)} for r in rows]
    grand_total = sum(r["total"] for r in breakdown)

    return {
        "period": f"{year}-{str(month).zfill(2)}",
        "breakdown": sorted(breakdown, key=lambda x: x["total"], reverse=True),
        "total": grand_total,
    }
