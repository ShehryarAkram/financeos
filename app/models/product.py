import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from decimal import Decimal

class Product(Base):
    """
    Product catalog — admin pre-adds items.
    When making an invoice, type short name → auto-fills description + price.
    """
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(255))           # full name: "Basmati Rice 1kg"
    short_name: Mapped[str] = mapped_column(String(50))      # quick search: "rice", "daal", "kapra"
    description: Mapped[str | None] = mapped_column(Text)
    default_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    unit: Mapped[str] = mapped_column(String(20), default="piece")  # piece, kg, meter, litre, dozen

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
