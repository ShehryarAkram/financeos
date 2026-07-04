"""
Invoice Service
- Create invoice + auto journal entry
- Generate PDF
- Send via WhatsApp
- Mark as paid
"""

import uuid
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.invoice import Invoice, InvoiceLine, InvoiceStatus, TaxType
from app.models.contact import Contact
from app.models.account import Account
from app.models.journal import EntrySource
from app.services.journal_service import JournalService
import io


class InvoiceService:

    @staticmethod
    def get_next_number(org_id, db: Session) -> str:
        """Auto-increment invoice number per org: INV-2026-001"""
        year = date.today().year
        count = db.query(func.count(Invoice.id)).filter(
            Invoice.org_id == org_id
        ).scalar() or 0
        return f"INV-{year}-{str(count + 1).zfill(3)}"

    @staticmethod
    def create_invoice(
        db: Session,
        org_id: uuid.UUID,
        contact_id: uuid.UUID,
        lines: list[dict],       # [{"description": "Kapra", "quantity": 10, "unit_price": 500}]
        due_days: int = 30,
        tax_type: TaxType = TaxType.none,
        notes: str | None = None,
    ) -> Invoice:
        """Create invoice, calculate totals, auto-create journal entry"""

        # Calculate totals
        subtotal = Decimal("0")
        for line in lines:
            qty = Decimal(str(line.get("quantity", 1)))
            price = Decimal(str(line["unit_price"]))
            line["line_total"] = float(qty * price)
            subtotal += qty * price

        # Tax calculation
        tax_amount = Decimal("0")
        if tax_type == TaxType.sales_tax_17:
            tax_amount = subtotal * Decimal("0.17")

        total = subtotal + tax_amount
        today = date.today()

        invoice = Invoice(
            org_id=org_id,
            contact_id=contact_id,
            invoice_number=InvoiceService.get_next_number(org_id, db),
            status=InvoiceStatus.draft,
            issue_date=today,
            due_date=today + timedelta(days=due_days),
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            tax_type=tax_type,
            notes=notes,
        )
        db.add(invoice)
        db.flush()

        # Add line items
        for line in lines:
            il = InvoiceLine(
                invoice_id=invoice.id,
                description=line["description"],
                quantity=Decimal(str(line.get("quantity", 1))),
                unit_price=Decimal(str(line["unit_price"])),
                line_total=Decimal(str(line["line_total"])),
            )
            db.add(il)

        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def post_invoice(invoice: Invoice, db: Session) -> Invoice:
        """
        Post invoice = make it official.
        Creates journal entry: DR Accounts Receivable / CR Sales Revenue
        """
        if invoice.status != InvoiceStatus.draft:
            return invoice

        # Get accounts
        ar = db.query(Account).filter(
            Account.org_id == invoice.org_id,
            Account.code == "1003"
        ).first()
        rev = db.query(Account).filter(
            Account.org_id == invoice.org_id,
            Account.code == "4001"
        ).first()

        entry = JournalService.create_entry(
            db=db,
            org_id=invoice.org_id,
            entry_date=invoice.issue_date,
            reference=invoice.invoice_number,
            narration=f"Invoice {invoice.invoice_number}",
            source=EntrySource.invoice,
            lines=[
                {"account_id": ar.id,  "debit": invoice.total, "credit": 0,
                 "contact_id": invoice.contact_id},
                {"account_id": rev.id, "debit": 0, "credit": invoice.subtotal},
            ],
        )

        invoice.status = InvoiceStatus.sent
        invoice.journal_entry_id = entry.id

        # Update contact AR balance
        if invoice.contact_id:
            contact = db.get(Contact, invoice.contact_id)
            if contact:
                contact.udhar_balance = float(
                    Decimal(str(contact.udhar_balance)) + invoice.total
                )

        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def record_payment(
        invoice: Invoice,
        amount: Decimal,
        db: Session,
    ) -> Invoice:
        """Record full or partial payment against invoice"""
        cash = db.query(Account).filter(
            Account.org_id == invoice.org_id,
            Account.code == "1001"
        ).first()
        ar = db.query(Account).filter(
            Account.org_id == invoice.org_id,
            Account.code == "1003"
        ).first()

        JournalService.create_entry(
            db=db,
            org_id=invoice.org_id,
            entry_date=date.today(),
            reference=f"PMT-{invoice.invoice_number}",
            narration=f"Payment for {invoice.invoice_number}",
            source=EntrySource.invoice,
            lines=[
                {"account_id": cash.id, "debit": amount,  "credit": 0},
                {"account_id": ar.id,   "debit": 0, "credit": amount,
                 "contact_id": invoice.contact_id},
            ],
        )

        invoice.amount_paid = Decimal(str(invoice.amount_paid)) + amount
        invoice.status = (
            InvoiceStatus.paid if invoice.amount_paid >= invoice.total
            else InvoiceStatus.partial
        )
        if invoice.status == InvoiceStatus.paid:
            invoice.paid_date = date.today()
            contact = db.get(Contact, invoice.contact_id)
            if contact:
                contact.udhar_balance = float(
                    Decimal(str(contact.udhar_balance)) - amount
                )

        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def generate_pdf(invoice: Invoice, db: Session) -> bytes:
        """Generate professional invoice PDF using reportlab"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.enums import TA_RIGHT, TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=15*mm, leftMargin=15*mm,
                                topMargin=15*mm, bottomMargin=15*mm)

        styles = getSampleStyleSheet()
        green = colors.HexColor("#16a34a")
        dark = colors.HexColor("#111827")
        gray = colors.HexColor("#6b7280")

        contact = db.get(Contact, invoice.contact_id)
        from app.models.organization import Organization
        org = db.get(Organization, invoice.org_id)

        elements = []

        # Header
        header_data = [
            [Paragraph(f"<font size=20 color='#16a34a'><b>{org.name}</b></font>", styles["Normal"]),
             Paragraph(f"<font size=20><b>INVOICE</b></font>", ParagraphStyle("r", alignment=TA_RIGHT, fontSize=20))],
            [Paragraph(f"<font size=9 color='#6b7280'>{org.city or ''} | {org.phone or ''}</font>", styles["Normal"]),
             Paragraph(f"<font size=9 color='#6b7280'>{invoice.invoice_number}</font>",
                       ParagraphStyle("r2", alignment=TA_RIGHT, fontSize=9))],
        ]
        header = Table(header_data, colWidths=[95*mm, 85*mm])
        header.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
        elements.append(header)
        elements.append(Spacer(1, 8*mm))

        # Bill to + dates
        info_data = [
            [Paragraph("<b>Bill To:</b>", styles["Normal"]),
             Paragraph("<b>Invoice Date:</b>", styles["Normal"]),
             Paragraph(str(invoice.issue_date), styles["Normal"])],
            [Paragraph(f"<b>{contact.name if contact else ''}</b>", styles["Normal"]),
             Paragraph("<b>Due Date:</b>", styles["Normal"]),
             Paragraph(str(invoice.due_date), styles["Normal"])],
            [Paragraph(contact.phone or "" if contact else "", styles["Normal"]),
             Paragraph("<b>Status:</b>", styles["Normal"]),
             Paragraph(f"<b>{invoice.status.value.upper()}</b>", styles["Normal"])],
        ]
        info = Table(info_data, colWidths=[80*mm, 40*mm, 60*mm])
        elements.append(info)
        elements.append(Spacer(1, 8*mm))

        # Line items table
        db.refresh(invoice)
        item_data = [["Description", "Qty", "Unit Price", "Total"]]
        for line in invoice.lines:
            item_data.append([
                line.description,
                str(line.quantity),
                f"Rs. {line.unit_price:,.2f}",
                f"Rs. {line.line_total:,.2f}",
            ])

        item_table = Table(item_data, colWidths=[90*mm, 20*mm, 40*mm, 30*mm])
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), green),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f9fafb")]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 6*mm))

        # Totals
        totals_data = [
            ["", "Subtotal:", f"Rs. {invoice.subtotal:,.2f}"],
        ]
        if invoice.tax_amount > 0:
            totals_data.append(["", "Tax:", f"Rs. {invoice.tax_amount:,.2f}"])
        totals_data.append(["", "TOTAL:", f"Rs. {invoice.total:,.2f}"])

        totals = Table(totals_data, colWidths=[90*mm, 50*mm, 40*mm])
        totals.setStyle(TableStyle([
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
            ("FONTNAME", (1,-1), (-1,-1), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("LINEABOVE", (1,-1), (-1,-1), 1, dark),
        ]))
        elements.append(totals)

        if invoice.notes:
            elements.append(Spacer(1, 6*mm))
            elements.append(Paragraph(f"<b>Notes:</b> {invoice.notes}", styles["Normal"]))

        # Footer
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph(
            "<font size=8 color='#6b7280'>Generated by FinanceOS — Pakistan ka apna hisaab kitab</font>",
            ParagraphStyle("footer", alignment=TA_CENTER, fontSize=8)
        ))

        doc.build(elements)
        return buffer.getvalue()
