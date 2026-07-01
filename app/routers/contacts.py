"""
Contacts Router — customers and suppliers, full CRUD.
This is the foundation other features (Udhar Book, Invoices) depend on.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.contact import Contact, ContactType

router = APIRouter()


class ContactCreate(BaseModel):
    org_id: str
    name: str
    contact_type: str = "customer"   # customer | supplier | both
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    ntn: Optional[str] = None
    notes: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    contact_type: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    ntn: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


def contact_to_dict(c: Contact) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "contact_type": c.contact_type.value,
        "phone": c.phone,
        "whatsapp": c.whatsapp,
        "email": c.email,
        "address": c.address,
        "ntn": c.ntn,
        "udhar_balance": float(c.udhar_balance),
        "notes": c.notes,
        "is_active": c.is_active,
        "created_at": str(c.created_at),
    }


@router.get("/list")
def list_contacts(org_id: str, contact_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Contact).filter(
        Contact.org_id == uuid.UUID(org_id),
        Contact.is_active == True,
    )
    if contact_type:
        query = query.filter(Contact.contact_type == ContactType(contact_type))

    contacts = query.order_by(Contact.name).all()
    return [contact_to_dict(c) for c in contacts]


@router.post("/create")
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    org_id = uuid.UUID(payload.org_id)

    # Prevent duplicate phone within same org
    if payload.phone:
        existing = db.query(Contact).filter(
            Contact.org_id == org_id,
            Contact.phone == payload.phone,
        ).first()
        if existing:
            raise HTTPException(400, "A contact with this phone number already exists")

    contact = Contact(
        org_id=org_id,
        name=payload.name,
        contact_type=ContactType(payload.contact_type),
        phone=payload.phone,
        whatsapp=payload.whatsapp or payload.phone,
        email=payload.email,
        address=payload.address,
        ntn=payload.ntn,
        notes=payload.notes,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact_to_dict(contact)


@router.get("/{contact_id}")
def get_contact(contact_id: str, db: Session = Depends(get_db)):
    contact = db.get(Contact, uuid.UUID(contact_id))
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact_to_dict(contact)


@router.patch("/{contact_id}")
def update_contact(contact_id: str, payload: ContactUpdate, db: Session = Depends(get_db)):
    contact = db.get(Contact, uuid.UUID(contact_id))
    if not contact:
        raise HTTPException(404, "Contact not found")

    data = payload.model_dump(exclude_unset=True)
    if "contact_type" in data:
        data["contact_type"] = ContactType(data["contact_type"])

    for key, value in data.items():
        setattr(contact, key, value)

    db.commit()
    db.refresh(contact)
    return contact_to_dict(contact)


@router.delete("/{contact_id}")
def delete_contact(contact_id: str, db: Session = Depends(get_db)):
    """Soft delete — keeps transaction history intact"""
    contact = db.get(Contact, uuid.UUID(contact_id))
    if not contact:
        raise HTTPException(404, "Contact not found")

    if contact.udhar_balance != 0:
        raise HTTPException(400, f"Cannot delete contact with outstanding balance of Rs. {contact.udhar_balance:,.0f}")

    contact.is_active = False
    db.commit()
    return {"status": "deleted"}

@router.get("/udhar/list")
def list_udhar(org_id: str, db: Session = Depends(get_db)):
    """Contacts with outstanding udhar balance, sorted highest first"""
    contacts = db.query(Contact).filter(
        Contact.org_id == uuid.UUID(org_id),
        Contact.is_active == True,
        Contact.udhar_balance > 0,
    ).order_by(Contact.udhar_balance.desc()).all()

    total = sum(float(c.udhar_balance) for c in contacts)

    return {
        "total_udhar": total,
        "contact_count": len(contacts),
        "contacts": [contact_to_dict(c) for c in contacts],
    }


class ReminderRequest(BaseModel):
    org_id: str


@router.post("/{contact_id}/send-reminder")
async def send_udhar_reminder(contact_id: str, payload: ReminderRequest, db: Session = Depends(get_db)):
    from app.services.whatsapp_service import WhatsAppService

    contact = db.get(Contact, uuid.UUID(contact_id))
    if not contact:
        raise HTTPException(404, "Contact not found")
    if not contact.whatsapp:
        raise HTTPException(400, "Contact has no WhatsApp number on file")
    if contact.udhar_balance <= 0:
        raise HTTPException(400, "Contact has no outstanding balance")

    sent = await WhatsAppService.send_reminder(
        to=contact.whatsapp,
        contact_name=contact.name,
        amount=float(contact.udhar_balance),
        custom_message=contact.custom_reminder_message,
    )

    if sent:
        contact.last_reminder_at = __import__("datetime").datetime.utcnow()
        db.commit()

    return {"status": "sent" if sent else "failed", "amount": float(contact.udhar_balance)}
