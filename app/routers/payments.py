from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, PaymentStatus, User, OrderStatus
from app.auth.jwt_handler import get_current_active_user
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"]) 
ps = PaymentService()


@router.post("/checkout")
def checkout(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    url = ps.create_checkout(order.id, order.total_amount)
    return {"checkout_url": url}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    signature = request.headers.get("X-Signature")
    if not ps.verify_webhook(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook")
    order_id = payload.get("order_id")
    status = payload.get("status")
    order = db.query(Order).filter(Order.id == order_id).first()
    if order:
        normalized = status if status in {PaymentStatus.unpaid, PaymentStatus.paid, PaymentStatus.failed, PaymentStatus.refunded} else PaymentStatus.paid
        order.payment_status = normalized
        if normalized == PaymentStatus.paid:
            order.status = OrderStatus.paid
        db.add(order)
        db.commit()
    return {"ok": True}


@router.get("/status/{order_id}")
def payment_status(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"payment_status": order.payment_status}