from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, OrderItem, Product, Coupon, User, OrderStatus, PaymentStatus
from app.schemas import OrderCreate, OrderOut, OrderStatusUpdate
from app.auth.jwt_handler import get_current_active_user, get_current_admin
from app.services.email_service import send_order_confirmation

router = APIRouter(prefix="/orders", tags=["Orders"])


def _apply_coupon(db: Session, amount: float, code: str, product_ids: List[int]) -> float:
    coupon = db.query(Coupon).filter(Coupon.code == code).first()
    if not coupon:
        return 0.0
    today = datetime.utcnow().date()
    if coupon.valid_from and today < coupon.valid_from:
        return 0.0
    if coupon.valid_to and today > coupon.valid_to:
        return 0.0
    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        return 0.0
    if coupon.applicable_products:
        if not any(pid in coupon.applicable_products for pid in product_ids):
            return 0.0
    discount = amount * (coupon.discount_value / 100.0) if coupon.discount_type == "percent" else coupon.discount_value
    coupon.used_count += 1
    db.add(coupon)
    return min(discount, amount)


@router.post("/", response_model=OrderOut)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db), bg: BackgroundTasks = None, user: User = Depends(get_current_active_user)):
    # Calculate and validate stock
    product_ids = [i.product_id for i in order_in.items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}
    if len(products) != len(product_ids):
        raise HTTPException(status_code=400, detail="Invalid product(s)")

    total = 0.0
    items: List[OrderItem] = []
    for it in order_in.items:
        prod = products[it.product_id]
        if prod.stock < it.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {prod.name}")
        total += prod.price * it.quantity
        items.append(OrderItem(product_id=prod.id, quantity=it.quantity, unit_price=prod.price))

    discount = 0.0
    if order_in.coupon_code:
        discount = _apply_coupon(db, total, order_in.coupon_code, product_ids)

    order = Order(
        user_id=user.id,
        total_amount=round(total - discount, 2),
        discount=round(discount, 2),
        status=OrderStatus.pending,
        payment_status=PaymentStatus.unpaid,
        shipping_address=order_in.shipping_address,
    )
    db.add(order)
    db.flush()  # get order.id

    # Persist items and reduce stock
    for oi in items:
        oi.order_id = order.id
        db.add(oi)
        prod = products[oi.product_id]
        prod.stock -= oi.quantity
        db.add(prod)

    db.commit()
    db.refresh(order)

    if bg:
        bg.add_task(send_order_confirmation, user.email, order.id)

    return OrderOut(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        discount=order.discount,
        status=order.status,
        payment_status=order.payment_status,
        shipping_address=order.shipping_address,
        tracking_id=order.tracking_id,
        created_at=order.created_at,
        items=[{"product_id": oi.product_id, "quantity": oi.quantity, "unit_price": oi.unit_price} for oi in order.items],
    )


@router.get("/", response_model=list[OrderOut])
def list_my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    outs = []
    for o in orders:
        outs.append(OrderOut(
            id=o.id,
            user_id=o.user_id,
            total_amount=o.total_amount,
            discount=o.discount,
            status=o.status,
            payment_status=o.payment_status,
            shipping_address=o.shipping_address,
            tracking_id=o.tracking_id,
            created_at=o.created_at,
            items=[{"product_id": oi.product_id, "quantity": oi.quantity, "unit_price": oi.unit_price} for oi in o.items],
        ))
    return outs


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o or (o.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut(
        id=o.id,
        user_id=o.user_id,
        total_amount=o.total_amount,
        discount=o.discount,
        status=o.status,
        payment_status=o.payment_status,
        shipping_address=o.shipping_address,
        tracking_id=o.tracking_id,
        created_at=o.created_at,
        items=[{"product_id": oi.product_id, "quantity": oi.quantity, "unit_price": oi.unit_price} for oi in o.items],
    )


@router.patch("/{order_id}/status")
def update_order_status(order_id: int, upd: OrderStatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_admin)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")
    o.status = upd.status
    db.add(o)
    db.commit()
    return {"detail": "Order status updated"}


@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o or (o.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Order not found")
    if o.status in [OrderStatus.cancelled, OrderStatus.delivered]:
        raise HTTPException(status_code=400, detail="Cannot cancel this order")
    o.status = OrderStatus.cancelled
    db.add(o)
    db.commit()
    return {"detail": "Order cancelled"}


@router.get("/admin/orders", response_model=list[OrderOut])
def admin_list_orders(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [
        OrderOut(
            id=o.id,
            user_id=o.user_id,
            total_amount=o.total_amount,
            discount=o.discount,
            status=o.status,
            payment_status=o.payment_status,
            shipping_address=o.shipping_address,
            tracking_id=o.tracking_id,
            created_at=o.created_at,
            items=[{"product_id": oi.product_id, "quantity": oi.quantity, "unit_price": oi.unit_price} for oi in o.items],
        ) for o in orders
    ]


@router.post("/auto-cancel")
def auto_cancel_unpaid(older_than_minutes: int = 60, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
    q = db.query(Order).filter(
        Order.status == OrderStatus.pending,
        Order.payment_status == PaymentStatus.unpaid,
        Order.created_at < cutoff,
    )
    count = 0
    for o in q.all():
        o.status = OrderStatus.cancelled
        db.add(o)
        count += 1
    db.commit()
    return {"cancelled": count, "older_than_minutes": older_than_minutes}


@router.get("/{order_id}/invoice")
def get_invoice(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o or (o.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Order not found")
    items = [
        {"product_id": oi.product_id, "quantity": oi.quantity, "unit_price": oi.unit_price, "line_total": round(oi.unit_price * oi.quantity, 2)}
        for oi in o.items
    ]
    subtotal = round(sum(i["line_total"] for i in items), 2)
    discount = round(o.discount or 0.0, 2)
    total = round(subtotal - discount, 2)
    return {
        "invoice_number": f"INV-{o.id}",
        "order_id": o.id,
        "user_id": o.user_id,
        "status": o.status,
        "payment_status": o.payment_status,
        "created_at": o.created_at,
        "items": items,
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
    }