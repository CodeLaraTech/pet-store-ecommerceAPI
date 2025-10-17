from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Product, Order, OrderItem
from app.auth.jwt_handler import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"]) 


@router.get("/users")
def admin_users(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.get("/products")
def admin_products(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return db.query(Product).order_by(Product.created_at.desc()).all()


@router.get("/orders")
def admin_orders(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.get("/sales-stats")
def sales_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    species: Optional[str] = None,
):
    q = db.query(Order)
    if start_date:
        q = q.filter(func.date(Order.created_at) >= start_date)
    if end_date:
        q = q.filter(func.date(Order.created_at) <= end_date)

    # Aggregate revenue and count
    total_orders = q.count()
    revenue = db.query(func.coalesce(func.sum(Order.total_amount), 0.0))
    if start_date:
        revenue = revenue.filter(func.date(Order.created_at) >= start_date)
    if end_date:
        revenue = revenue.filter(func.date(Order.created_at) <= end_date)
    revenue = revenue.scalar() or 0.0

    # Top categories by species (approximate from Product.species_tags)
    items_q = db.query(Product.name, Product.species_tags, func.sum(OrderItem.quantity).label("sold")) \
        .join(OrderItem, OrderItem.product_id == Product.id) \
        .join(Order, OrderItem.order_id == Order.id)
    if start_date:
        items_q = items_q.filter(func.date(Order.created_at) >= start_date)
    if end_date:
        items_q = items_q.filter(func.date(Order.created_at) <= end_date)
    items_q = items_q.group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc())
    items = items_q.limit(10).all()

    if species:
        items = [i for i in items if i[1] and species in i[1]]

    return {
        "total_orders": int(total_orders),
        "revenue": float(revenue),
        "top_items": [{"name": name, "sold": int(sold)} for name, _, sold in items],
    }


@router.get("/notifications/low-stock")
def low_stock(db: Session = Depends(get_db), _: User = Depends(get_current_admin), threshold: int = 5):
    items = db.query(Product).filter(Product.stock <= threshold).order_by(Product.stock.asc()).all()
    return {"low_stock": [{"id": p.id, "name": p.name, "stock": p.stock} for p in items], "threshold": threshold}