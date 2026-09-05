from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime, date
import uuid

from app.core.database import get_db
from app.models.order import Order, OrderItem, OrderStatus, OrderChannel, PaymentMethod
from app.models.contact import Contact
from app.models.account import Account
from app.models.journal import EntrySource
from app.services.journal_service import JournalService

router = APIRouter()

class OrderItemIn(BaseModel):
    description: str
    quantity: int = 1
    buying_price: float = 0
    selling_price: float
    product_id: Optional[str] = None

class OrderCreate(BaseModel):
    org_id: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    city: Optional[str] = None
    contact_id: Optional[str] = None
    supplier_id: Optional[str] = None
    channel: str = "whatsapp"
    payment_method: str = "cod"
    shipping_charges: float = 0
    discount: float = 0
    notes: Optional[str] = None
    items: list[OrderItemIn]

def next_order_number(org_id, db: Session) -> str:
    count = db.query(func.count(Order.id)).filter(Order.org_id == org_id).scalar() or 0
    return f"DS-{date.today().year}-{str(count+1).zfill(4)}"

def order_to_dict(o: Order, db: Session) -> dict:
    items = [{
        "id": str(i.id), "description": i.description,
        "quantity": i.quantity, "buying_price": float(i.buying_price),
        "selling_price": float(i.selling_price),
        "line_total": float(i.line_total), "margin": float(i.margin),
    } for i in o.items]

    contact = db.get(Contact, o.contact_id) if o.contact_id else None
    return {
        "id": str(o.id), "order_number": o.order_number,
        "status": o.status.value, "channel": o.channel.value,
        "payment_method": o.payment_method.value,
        "customer_name": o.customer_name or (contact.name if contact else "Walk-in"),
        "customer_phone": o.customer_phone or (contact.phone if contact else None),
        "customer_address": o.customer_address, "city": o.city,
        "subtotal": float(o.subtotal), "shipping_charges": float(o.shipping_charges),
        "discount": float(o.discount), "total": float(o.total),
        "buying_total": float(o.buying_total), "margin": float(o.margin),
        "cod_collected": o.cod_collected,
        "tracking_number": o.tracking_number, "courier": o.courier,
        "expected_delivery": str(o.expected_delivery) if o.expected_delivery else None,
        "notes": o.notes, "items": items,
        "created_at": str(o.created_at),
    }

@router.get("/list")
def list_orders(
    org_id: str,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Order).filter(Order.org_id == uuid.UUID(org_id))
    if status: query = query.filter(Order.status == OrderStatus(status))
    if channel: query = query.filter(Order.channel == OrderChannel(channel))
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()
    return {"orders": [order_to_dict(o, db) for o in orders], "total": total}

@router.post("/create")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    org_id = uuid.UUID(payload.org_id)

    subtotal = sum(i.quantity * i.selling_price for i in payload.items)
    buying_total = sum(i.quantity * i.buying_price for i in payload.items)
    total = subtotal + payload.shipping_charges - payload.discount
    margin = subtotal - buying_total

    order = Order(
        org_id=org_id,
        order_number=next_order_number(org_id, db),
        contact_id=uuid.UUID(payload.contact_id) if payload.contact_id else None,
        supplier_id=uuid.UUID(payload.supplier_id) if payload.supplier_id else None,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_address=payload.customer_address,
        city=payload.city,
        channel=OrderChannel(payload.channel),
        payment_method=PaymentMethod(payload.payment_method),
        subtotal=Decimal(str(subtotal)),
        shipping_charges=Decimal(str(payload.shipping_charges)),
        discount=Decimal(str(payload.discount)),
        total=Decimal(str(total)),
        buying_total=Decimal(str(buying_total)),
        margin=Decimal(str(margin)),
        cod_amount=Decimal(str(total)) if payload.payment_method == "cod" else Decimal("0"),
        notes=payload.notes,
    )
    db.add(order); db.flush()

    for item in payload.items:
        line_total = Decimal(str(item.quantity * item.selling_price))
        item_margin = Decimal(str(item.quantity * (item.selling_price - item.buying_price)))
        oi = OrderItem(
            order_id=order.id,
            product_id=uuid.UUID(item.product_id) if item.product_id else None,
            description=item.description,
            quantity=item.quantity,
            buying_price=Decimal(str(item.buying_price)),
            selling_price=Decimal(str(item.selling_price)),
            line_total=line_total,
            margin=item_margin,
        )
        db.add(oi)

    db.commit(); db.refresh(order)
    return order_to_dict(order, db)

@router.patch("/{order_id}/status")
def update_status(order_id: str, payload: dict, db: Session = Depends(get_db)):
    order = db.get(Order, uuid.UUID(order_id))
    if not order: raise HTTPException(404, "Order not found")

    new_status = OrderStatus(payload["status"])
    order.status = new_status

    if payload.get("tracking_number"):
        order.tracking_number = payload["tracking_number"]
    if payload.get("courier"):
        order.courier = payload["courier"]

    # Auto journal entry when COD collected
    if new_status == OrderStatus.cod_collected and not order.cod_collected:
        order.cod_collected = True
        order.cod_collected_at = datetime.utcnow()
        order.delivered_at = order.delivered_at or datetime.utcnow()

        cash = db.query(Account).filter(
            Account.org_id == order.org_id, Account.code == "1001"
        ).first()
        revenue = db.query(Account).filter(
            Account.org_id == order.org_id, Account.code == "4001"
        ).first()

        if cash and revenue:
            entry = JournalService.create_entry(
                db=db, org_id=order.org_id,
                entry_date=date.today(),
                reference=order.order_number,
                narration=f"COD collected — {order.order_number}",
                source=EntrySource.invoice,
                lines=[
                    {"account_id": cash.id, "debit": order.total, "credit": 0},
                    {"account_id": revenue.id, "debit": 0, "credit": order.total},
                ],
            )
            order.journal_entry_id = entry.id

    db.commit(); db.refresh(order)
    return order_to_dict(order, db)

@router.get("/dashboard/{org_id}")
def orders_dashboard(org_id: str, db: Session = Depends(get_db)):
    oid = uuid.UUID(org_id)
    today = date.today()

    today_orders = db.query(func.count(Order.id)).filter(
        Order.org_id == oid,
        func.date(Order.created_at) == today
    ).scalar() or 0

    today_revenue = db.query(func.sum(Order.total)).filter(
        Order.org_id == oid,
        Order.cod_collected == True,
        func.date(Order.cod_collected_at) == today
    ).scalar() or 0

    pending_cod = db.query(func.sum(Order.cod_amount)).filter(
        Order.org_id == oid,
        Order.payment_method == PaymentMethod.cod,
        Order.cod_collected == False,
        Order.status.in_([OrderStatus.delivered, OrderStatus.out_for_delivery])
    ).scalar() or 0

    by_status = db.query(Order.status, func.count(Order.id)).filter(
        Order.org_id == oid
    ).group_by(Order.status).all()

    return {
        "today_orders": today_orders,
        "today_revenue": float(today_revenue),
        "pending_cod": float(pending_cod),
        "by_status": {s.value: c for s, c in by_status},
    }

@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.get(Order, uuid.UUID(order_id))
    if not order: raise HTTPException(404, "Order not found")
    return order_to_dict(order, db)
