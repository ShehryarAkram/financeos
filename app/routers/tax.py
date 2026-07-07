"""
FBR Tax Router
- WHT calculator
- Sales tax on invoices
- Monthly tax summary
- Tax settings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
import uuid
from datetime import date

from app.core.database import get_db
from app.models.organization import Organization
from app.models.journal import JournalEntry, JournalLine
from app.models.account import Account, AccountType
from app.models.invoice import Invoice, TaxType
from app.services.tax_service import (
    calculate_wht, calculate_sales_tax,
    WHTSection, SalesTaxRate
)

router = APIRouter()


class WHTRequest(BaseModel):
    amount: float
    section: str = "153a"
    supplier_is_filer: bool = False


class TaxSettingsUpdate(BaseModel):
    ntn: Optional[str] = None
    strn: Optional[str] = None
    is_tax_filer: Optional[bool] = None
    sales_tax_registered: Optional[bool] = None
    sales_tax_rate: Optional[float] = None


@router.get("/settings/{org_id}")
def get_tax_settings(org_id: str, db: Session = Depends(get_db)):
    org = db.get(Organization, uuid.UUID(org_id))
    if not org:
        raise HTTPException(404, "Organization not found")
    return {
        "org_id": str(org.id),
        "ntn": org.ntn,
        "strn": org.strn,
        "is_tax_filer": org.is_tax_filer,
        "sales_tax_registered": org.sales_tax_registered,
        "sales_tax_rate": float(org.sales_tax_rate) if org.sales_tax_rate else 17.0,
    }


@router.patch("/settings/{org_id}")
def update_tax_settings(org_id: str, payload: TaxSettingsUpdate, db: Session = Depends(get_db)):
    org = db.get(Organization, uuid.UUID(org_id))
    if not org:
        raise HTTPException(404, "Organization not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(org, k, v)

    db.commit()
    db.refresh(org)
    return {"status": "updated", "ntn": org.ntn, "strn": org.strn}


@router.post("/calculate-wht")
def wht_calculator(payload: WHTRequest):
    """Calculate WHT on any payment amount"""
    try:
        section = WHTSection(payload.section)
    except ValueError:
        raise HTTPException(400, f"Invalid section. Use: 153a, 153b, 236g, none")

    return calculate_wht(
        amount=Decimal(str(payload.amount)),
        section=section,
        supplier_is_filer=payload.supplier_is_filer,
    )


@router.post("/calculate-sales-tax")
def sales_tax_calculator(payload: dict):
    """Calculate GST on any amount"""
    amount = Decimal(str(payload.get("amount", 0)))
    rate = float(payload.get("rate", 17.0))
    return calculate_sales_tax(amount, rate)


@router.get("/monthly-summary/{org_id}")
def monthly_tax_summary(
    org_id: str,
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """Monthly tax summary for FBR return filing"""
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    from_date = date(year, month, 1)
    to_date = date(year, month, last_day)

    # Get income and expense totals
    rows = (
        db.query(
            Account.type,
            Account.code,
            func.sum(JournalLine.debit).label("total_debit"),
            func.sum(JournalLine.credit).label("total_credit"),
        )
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
        .filter(
            JournalEntry.org_id == uuid.UUID(org_id),
            JournalEntry.is_posted == True,
            JournalEntry.date >= from_date,
            JournalEntry.date <= to_date,
        )
        .group_by(Account.type, Account.code)
        .all()
    )

    total_sales = Decimal("0")
    total_purchases = Decimal("0")
    sales_tax_collected = Decimal("0")
    wht_deducted = Decimal("0")

    for row in rows:
        debit = row.total_debit or Decimal("0")
        credit = row.total_credit or Decimal("0")

        if row.type == AccountType.income:
            total_sales += credit - debit
        elif row.type == AccountType.expense:
            total_purchases += debit - credit
        elif row.code == "2002":  # Sales Tax Payable
            sales_tax_collected += credit - debit
        elif row.code == "2003":  # WHT Payable
            wht_deducted += credit - debit

    # Invoice count for the period
    invoice_count = db.query(func.count(Invoice.id)).filter(
        Invoice.org_id == uuid.UUID(org_id),
        Invoice.issue_date >= from_date,
        Invoice.issue_date <= to_date,
        Invoice.status != "void",
    ).scalar() or 0

    return {
        "period": f"{year}-{str(month).zfill(2)}",
        "from_date": str(from_date),
        "to_date": str(to_date),
        "total_sales": float(total_sales),
        "total_purchases": float(total_purchases),
        "sales_tax_collected": float(sales_tax_collected),
        "wht_deducted": float(wht_deducted),
        "net_tax_payable": float(sales_tax_collected - wht_deducted),
        "invoice_count": invoice_count,
        "note": "This summary is for reference. Consult your CA for actual FBR filing."
    }
