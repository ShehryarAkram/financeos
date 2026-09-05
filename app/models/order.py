import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Boolean, ForeignKey, Numeric, Text, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum

class OrderStatus(str, enum.Enum):
    pending = "pending"
    supplier_ordered = "supplier_ordered"
    shipped = "shipped"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cod_collected = "cod_collected"
    returned = "returned"
    cancelled = "cancelled"

class OrderChannel(str, enum.Enum):
    whatsapp = "whatsapp"
    instagram = "instagram"
    tiktok = "tiktok"
    facebook = "facebook"
    website = "website"
    referral = "referral"
    walk_in = "walk_in"

class PaymentMethod(str, enum.Enum):
    cod = "cod"
    jazzcash = "jazzcash"
    easypaisa = "easypaisa"
    bank_transfer = "bank_transfer"
    card = "card"

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)

    order_number: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending, index=True)
    channel: Mapped[OrderChannel] = mapped_column(Enum(OrderChannel), default=OrderChannel.whatsapp)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), default=PaymentMethod.cod)

    # Customer info (denormalized for walk-ins without contact)
    customer_name: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(20))
    customer_address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))

    # Financials
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    shipping_charges: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    discount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    buying_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))  # supplier cost
    margin: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # COD tracking
    cod_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    cod_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    cod_collected_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Fulfillment
    supplier_order_ref: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(100))
    courier: Mapped[str | None] = mapped_column(String(50))  # leopards/tcs/blueex/trax
    expected_delivery: Mapped[date | None] = mapped_column(Date)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)

    notes: Mapped[str | None] = mapped_column(Text)
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)

    description: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    buying_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    margin: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    order: Mapped["Order"] = relationship("Order", back_populates="items")
