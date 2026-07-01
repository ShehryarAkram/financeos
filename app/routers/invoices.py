from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from app.core.database import get_db
from app.models.invoice import TaxType, InvoiceStatus
from app.models.contact import Contact
from app.services.invoice_service import InvoiceService
from app.services.whatsapp_service import WhatsAppService
import uuid

router = APIRouter()

class InvoiceLineIn(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float

class CreateInvoiceRequest(BaseModel):
    org_id: str
    contact_phone: str          # find or create contact by phone
    contact_name: str
    lines: list[InvoiceLineIn]
    due_days: int = 30
    tax_type: str = "none"
    notes: Optional[str] = None
    send_whatsapp: bool = True

@router.post("/create")
async def create_invoice(payload: CreateInvoiceRequest, db: Session = Depends(get_db)):
    org_id = uuid.UUID(payload.org_id)

    # Find or create contact
    contact = db.query(Contact).filter(
        Contact.org_id == org_id,
        Contact.phone == payload.contact_phone,
    ).first()
    if not contact:
        contact = Contact(
            org_id=org_id,
            name=payload.contact_name,
            phone=payload.contact_phone,
            whatsapp=payload.contact_phone,
        )
        db.add(contact)
        db.flush()

    # Create invoice
    lines = [{"description": l.description, "quantity": l.quantity,
               "unit_price": l.unit_price} for l in payload.lines]
    tax_type = TaxType(payload.tax_type) if payload.tax_type in TaxType.__members__ else TaxType.none

    invoice = InvoiceService.create_invoice(
        db=db, org_id=org_id, contact_id=contact.id,
        lines=lines, due_days=payload.due_days,
        tax_type=tax_type, notes=payload.notes,
    )

    # Post it (creates journal entry)
    invoice = InvoiceService.post_invoice(invoice, db)

    # Send WhatsApp notification
    if payload.send_whatsapp and contact.whatsapp:
        msg = (
            f"📄 *Invoice {invoice.invoice_number}*\n"
            f"Amount: *Rs. {invoice.total:,.0f}*\n"
            f"Due: {invoice.due_date}\n\n"
            f"Meherbani farma ke time par ada karein. 🙏"
        )
        await WhatsAppService.send_message(contact.whatsapp, msg)

    return {
        "invoice_number": invoice.invoice_number,
        "status": invoice.status,
        "total": float(invoice.total),
        "due_date": str(invoice.due_date),
        "contact": contact.name,
        "journal_entry_created": invoice.journal_entry_id is not None,
    }


@router.get("/{invoice_id}/pdf")
def download_pdf(invoice_id: str, db: Session = Depends(get_db)):
    from app.models.invoice import Invoice
    invoice = db.get(Invoice, uuid.UUID(invoice_id))
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    pdf = InvoiceService.generate_pdf(invoice, db)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}.pdf"})


@router.post("/{invoice_id}/pay")
def record_payment(invoice_id: str, payload: dict, db: Session = Depends(get_db)):
    from app.models.invoice import Invoice
    invoice = db.get(Invoice, uuid.UUID(invoice_id))
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    amount = Decimal(str(payload.get("amount", invoice.total)))
    invoice = InvoiceService.record_payment(invoice, amount, db)
    return {"status": invoice.status, "amount_paid": float(invoice.amount_paid),
            "amount_due": float(invoice.amount_due)}

@router.get("/list")
def list_invoices(org_id: str, db: Session = Depends(get_db)):
    from app.models.invoice import Invoice
    invoices = db.query(Invoice).filter(
        Invoice.org_id == uuid.UUID(org_id)
    ).order_by(Invoice.created_at.desc()).all()

    contact_ids = [inv.contact_id for inv in invoices]
    contacts = {c.id: c.name for c in db.query(Contact).filter(Contact.id.in_(contact_ids)).all()} if contact_ids else {}

    return [{
        "id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "contact": contacts.get(inv.contact_id, "Unknown"),
        "total": float(inv.total),
        "amount_paid": float(inv.amount_paid),
        "status": inv.status.value,
        "due_date": str(inv.due_date),
        "issue_date": str(inv.issue_date),
    } for inv in invoices]
