"""
WhatsApp Webhook Router — now wired to the database.

When a message comes in:
1. Parse intent via Groq NLP
2. Look up org by WhatsApp number
3. Route to journal service → creates real accounting entries
4. Update contact udhar balance
5. Reply in Urdu with confirmation
"""

from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from datetime import date, datetime
from app.core.database import get_db
from app.core.config import settings
from app.services.whatsapp_service import WhatsAppService, UrduNLPService
from app.services.journal_service import JournalService, JournalError
from app.models.user import User
from app.models.organization import Organization
from app.models.contact import Contact, ContactType
from app.models.account import Account, AccountType
from app.models.journal import JournalEntry, JournalLine, EntrySource

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_org_by_whatsapp(phone: str, db: Session) -> Organization | None:
    """Find org linked to this WhatsApp number"""
    user = db.query(User).filter(User.whatsapp_number == phone).first()
    if not user:
        return None
    from app.models.user import OrganizationUser
    membership = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == user.id,
        OrganizationUser.is_default_org == True,
    ).first()
    return membership.organization if membership else None


def get_or_create_contact(name: str, org_id, db: Session) -> Contact:
    """
    Find existing contact by name (case-insensitive).
    If not found, create with name only — no phone since we don't know it from the message.
    Bot-created contacts show up in Contacts page and can be updated with phone later.
    """
    contact = db.query(Contact).filter(
        Contact.org_id == org_id,
        Contact.name.ilike(name.strip()),
        Contact.is_active == True,
    ).first()
    if not contact:
        contact = Contact(
            org_id=org_id,
            name=name.strip(),
            contact_type=ContactType.customer,
        )
        db.add(contact)
        db.flush()
    return contact


def get_system_account(org_id, account_code: str, db: Session) -> Account | None:
    return db.query(Account).filter(
        Account.org_id == org_id,
        Account.code == account_code,
    ).first()


def get_daily_summary(org_id, db: Session) -> dict:
    """Calculate today's income, expense, profit and total udhar"""
    today = date.today()

    rows = (
        db.query(Account.type, func.sum(JournalLine.debit), func.sum(JournalLine.credit))
        .join(JournalLine, JournalLine.account_id == Account.id)
        .join(JournalEntry, JournalEntry.id == JournalLine.entry_id)
        .filter(
            JournalEntry.org_id == org_id,
            JournalEntry.date == today,
            JournalEntry.is_posted == True,
            Account.type.in_([AccountType.income, AccountType.expense, AccountType.asset]),
        )
        .group_by(Account.type)
        .all()
    )

    income = expense = Decimal("0")
    for acc_type, debit, credit in rows:
        d = debit or Decimal("0")
        c = credit or Decimal("0")
        if acc_type == AccountType.income:
            income += c - d
        elif acc_type == AccountType.expense:
            expense += d - c

    total_udhar = db.query(func.sum(Contact.udhar_balance)).filter(
        Contact.org_id == org_id,
        Contact.udhar_balance > 0,
    ).scalar() or 0

    return {
        "income": float(income),
        "expense": float(expense),
        "profit": float(income - expense),
        "total_udhar": float(total_udhar),
    }


# ── Webhook endpoints ─────────────────────────────────────────────────────────

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_message(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        from_number = message.get("from")
        msg_text = message.get("text", {}).get("body", "").strip()
        if not msg_text:
            return {"status": "empty"}

        # Look up org
        org = get_org_by_whatsapp(from_number, db)
        if not org:
            await WhatsAppService.send_message(from_number,
                "FinanceOS mein khush aamdeed! 🎉\nRegister karne ke liye app kholen.")
            return {"status": "unregistered"}

        # Parse and route
        intent = await UrduNLPService.parse_intent(msg_text)
        reply, result = await route_intent(intent, org, from_number, db)
        await WhatsAppService.send_message(from_number, reply)
        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}


async def route_intent(intent: dict, org: Organization, from_number: str, db: Session):
    """Route parsed intent to the correct journal service action"""
    i = intent.get("intent", "unknown")
    amount = Decimal(str(intent.get("amount") or 0))
    contact_name = intent.get("contact_name")
    if contact_name == "null": contact_name = None
    intent["contact_name"] = contact_name
    result = {}

    # Get core accounts (seeded on registration)
    cash = get_system_account(org.id, "1001", db)      # Cash in Hand
    ar   = get_system_account(org.id, "1003", db)      # Accounts Receivable
    rev  = get_system_account(org.id, "4001", db)      # Sales Revenue
    exp  = get_system_account(org.id, "5106", db)      # Miscellaneous Expense

    if i == "cash_income" and amount > 0:
        JournalService.create_entry(
            db=db, org_id=org.id,
            entry_date=date.today(),
            narration=intent.get("description") or "Cash income",
            narration_ur=intent.get("description_ur"),
            source=EntrySource.whatsapp_bot,
            lines=[
                {"account_id": cash.id, "debit": amount, "credit": 0},
                {"account_id": rev.id,  "debit": 0, "credit": amount},
            ],
        )

    elif i == "cash_expense" and amount > 0:
        JournalService.create_entry(
            db=db, org_id=org.id,
            entry_date=date.today(),
            narration=intent.get("description") or "Cash expense",
            narration_ur=intent.get("description_ur"),
            source=EntrySource.whatsapp_bot,
            lines=[
                {"account_id": exp.id,  "debit": amount, "credit": 0},
                {"account_id": cash.id, "debit": 0, "credit": amount},
            ],
        )

    elif i == "udhar_sale" and amount > 0 and contact_name:
        contact = get_or_create_contact(contact_name, org.id, db)
        JournalService.record_udhar_sale(
            db=db, org_id=org.id, amount=amount,
            ar_account_id=ar.id, revenue_account_id=rev.id,
            contact_id=contact.id,
            narration=f"Udhar sale to {contact_name}",
            narration_ur=intent.get("description_ur"),
        )
        db.refresh(contact)
        result["new_balance"] = float(contact.udhar_balance)

    elif i == "udhar_payment" and amount > 0 and contact_name:
        contact = get_or_create_contact(contact_name, org.id, db)
        JournalService.record_udhar_payment(
            db=db, org_id=org.id, amount=amount,
            cash_account_id=cash.id, ar_account_id=ar.id,
            contact_id=contact.id,
            narration=f"Udhar payment from {contact_name}",
        )
        db.refresh(contact)
        result["new_balance"] = float(contact.udhar_balance)

    elif i == "balance_query" and contact_name:
        contact = db.query(Contact).filter(
            Contact.org_id == org.id,
            Contact.name.ilike(contact_name),
        ).first()
        result["balance"] = float(contact.udhar_balance) if contact else 0

    elif i in ("daily_summary", "balance_query"):
        result = get_daily_summary(org.id, db)
        intent["intent"] = "daily_summary"

    reply = UrduNLPService.get_reply(intent, result)
    return reply, result


# ── Dev test endpoint (no WhatsApp needed) ────────────────────────────────────

@router.post("/test-nlp")
async def test_nlp(payload: dict):
    """Test NLP parsing only — no DB writes"""
    message = payload.get("message", "")
    intent = await UrduNLPService.parse_intent(message)
    # fix: bare "hisaab" should show as daily_summary
    if intent.get("intent") == "balance_query" and not intent.get("contact_name"):
        intent["intent"] = "daily_summary"
    reply = UrduNLPService.get_reply(intent)
    return {"intent": intent, "reply": reply}


@router.post("/test-full")
async def test_full(payload: dict, db: Session = Depends(get_db)):
    """
    Test full flow WITH database writes — simulates a real WhatsApp message.
    POST {"phone": "03001234567", "message": "Ahmed ka 2000 udhar"}
    """
    phone = payload.get("phone", "")
    message = payload.get("message", "")

    org = get_org_by_whatsapp(phone, db)
    if not org:
        # For testing: find org by phone on the organization itself
        user = db.query(User).filter(User.phone == phone).first()
        if user:
            from app.models.user import OrganizationUser
            m = db.query(OrganizationUser).filter(
                OrganizationUser.user_id == user.id
            ).first()
            org = m.organization if m else None

    if not org:
        return {"error": "No org found for this phone. Register first."}

    intent = await UrduNLPService.parse_intent(message)
    if intent.get("intent") == "balance_query" and not intent.get("contact_name"):
        intent["intent"] = "daily_summary"

    reply, result = await route_intent(intent, org, phone, db)
    return {"intent": intent, "result": result, "reply": reply}
