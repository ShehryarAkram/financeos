from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid
from app.core.database import get_db
from app.models.supplier import Supplier

router = APIRouter()

class SupplierCreate(BaseModel):
    org_id: str
    name: str
    platform: Optional[str] = None
    contact_name: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    avg_lead_time_days: int = 7
    reliability_score: int = 3
    notes: Optional[str] = None

def to_dict(s: Supplier) -> dict:
    return {
        "id": str(s.id), "name": s.name, "platform": s.platform,
        "contact_name": s.contact_name, "whatsapp": s.whatsapp,
        "email": s.email, "website": s.website,
        "avg_lead_time_days": s.avg_lead_time_days,
        "reliability_score": s.reliability_score,
        "notes": s.notes, "is_active": s.is_active,
    }

@router.get("/list")
def list_suppliers(org_id: str, db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).filter(
        Supplier.org_id == uuid.UUID(org_id),
        Supplier.is_active == True
    ).order_by(Supplier.name).all()
    return [to_dict(s) for s in suppliers]

@router.post("/create")
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)):
    s = Supplier(org_id=uuid.UUID(payload.org_id), **{k:v for k,v in payload.model_dump().items() if k != 'org_id'})
    db.add(s); db.commit(); db.refresh(s)
    return to_dict(s)

@router.patch("/{supplier_id}")
def update_supplier(supplier_id: str, payload: dict, db: Session = Depends(get_db)):
    s = db.get(Supplier, uuid.UUID(supplier_id))
    if not s: raise HTTPException(404, "Not found")
    for k, v in payload.items():
        if hasattr(s, k): setattr(s, k, v)
    db.commit(); db.refresh(s)
    return to_dict(s)

@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: str, db: Session = Depends(get_db)):
    s = db.get(Supplier, uuid.UUID(supplier_id))
    if not s: raise HTTPException(404, "Not found")
    s.is_active = False; db.commit()
    return {"status": "deleted"}
