from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.journal_service import JournalService
from datetime import date
import uuid

router = APIRouter()

@router.get("/pl")
def profit_and_loss(org_id: str, from_date: str, to_date: str, db: Session = Depends(get_db)):
    return JournalService.get_profit_and_loss(
        db=db,
        org_id=uuid.UUID(org_id),
        from_date=date.fromisoformat(from_date),
        to_date=date.fromisoformat(to_date),
    )

@router.get("/trial-balance")
def trial_balance(org_id: str, as_of: str = None, db: Session = Depends(get_db)):
    return JournalService.get_trial_balance(
        db=db,
        org_id=uuid.UUID(org_id),
        as_of=date.fromisoformat(as_of) if as_of else None,
    )

@router.get("/transactions")
def recent_transactions(org_id: str, limit: int = 20, db: Session = Depends(get_db)):
    from app.models.journal import JournalEntry, JournalLine
    from app.models.account import Account
    import uuid

    rows = (
        db.query(
            JournalEntry.date,
            JournalEntry.narration,
            JournalEntry.source,
            JournalLine.debit,
            JournalLine.credit,
            Account.name.label("account_name"),
            Account.type.label("account_type"),
        )
        .join(JournalLine, JournalLine.entry_id == JournalEntry.id)
        .join(Account, Account.id == JournalLine.account_id)
        .filter(
            JournalEntry.org_id == uuid.UUID(org_id),
            JournalEntry.is_posted == True,
            JournalLine.debit > 0,
        )
        .order_by(JournalEntry.date.desc(), JournalEntry.created_at.desc())
        .limit(limit)
        .all()
    )

    return [{
        "date": str(r.date),
        "narration": r.narration,
        "source": r.source.value,
        "amount": float(r.debit),
        "account": r.account_name,
        "type": r.account_type.value,
    } for r in rows]
