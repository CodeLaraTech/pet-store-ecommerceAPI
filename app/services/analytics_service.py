from typing import Dict, List
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User, Product, Order, OrderItem, Subscription, Pet


def get_overview(db: Session) -> Dict:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    revenue = db.query(func.coalesce(func.sum(Order.total_amount), 0.0)).scalar() or 0.0
    active_subs = db.query(func.count(Subscription.id)).scalar() or 0
    products = db.query(func.count(Product.id)).scalar() or 0
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "revenue": float(revenue),
        "active_subscriptions": active_subs,
        "products": products,
    }


def revenue_series(db: Session) -> Dict:
    rows = db.query(func.date(Order.created_at).label("day"), func.coalesce(func.sum(Order.total_amount), 0.0))\
        .group_by(func.date(Order.created_at)).order_by(func.date(Order.created_at)).all()
    return {"series": [{"day": str(day), "amount": float(amount)} for day, amount in rows]}


def top_products(db: Session) -> Dict:
    rows = db.query(Product.name, func.coalesce(func.sum(OrderItem.quantity), 0))\
        .join(OrderItem, OrderItem.product_id == Product.id)\
        .group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()
    return {"items": [{"name": name, "sold": int(sold)} for name, sold in rows]}


def species_trends(db: Session) -> Dict:
    rows = db.query(Pet.species, func.count(Subscription.id))\
        .join(Subscription, Subscription.pet_id == Pet.id)\
        .group_by(Pet.species).order_by(func.count(Subscription.id).desc()).all()
    return {"series": [{"species": species or "unknown", "subscriptions": int(cnt)} for species, cnt in rows]}


def subscription_churn(db: Session) -> Dict:
    total = db.query(func.count(Subscription.id)).scalar() or 0
    cancelled = db.query(func.count(Subscription.id)).filter(Subscription.status == "cancelled").scalar() or 0
    rate = (cancelled / total) * 100 if total else 0
    return {"total_subscriptions": total, "cancelled": cancelled, "churn_rate_percent": round(rate, 2)}