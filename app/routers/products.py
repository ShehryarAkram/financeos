from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
import uuid

from app.core.database import get_db
from app.models.product import Product

router = APIRouter()

class ProductCreate(BaseModel):
    org_id: str
    name: str
    short_name: str
    default_price: float
    unit: str = "piece"
    description: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    default_price: Optional[float] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None

def to_dict(p: Product) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "short_name": p.short_name,
        "default_price": float(p.default_price),
        "unit": p.unit,
        "description": p.description,
        "is_active": p.is_active,
    }

@router.get("/list")
def list_products(org_id: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(
        Product.org_id == uuid.UUID(org_id),
        Product.is_active == True,
    ).order_by(Product.short_name).all()
    return [to_dict(p) for p in products]

@router.post("/create")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        org_id=uuid.UUID(payload.org_id),
        name=payload.name,
        short_name=payload.short_name.lower().strip(),
        default_price=Decimal(str(payload.default_price)),
        unit=payload.unit,
        description=payload.description,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return to_dict(product)

@router.patch("/{product_id}")
def update_product(product_id: str, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, uuid.UUID(product_id))
    if not product:
        raise HTTPException(404, "Product not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(product, k, v)
    db.commit()
    db.refresh(product)
    return to_dict(product)

@router.delete("/{product_id}")
def delete_product(product_id: str, db: Session = Depends(get_db)):
    product = db.get(Product, uuid.UUID(product_id))
    if not product:
        raise HTTPException(404, "Product not found")
    product.is_active = False
    db.commit()
    return {"status": "deleted"}
