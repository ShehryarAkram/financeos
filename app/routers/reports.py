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
