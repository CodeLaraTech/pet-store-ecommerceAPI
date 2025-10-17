from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subscription, Product, Pet, User, Order, OrderItem, SubscriptionStatus, OrderStatus, PaymentStatus
from app.schemas import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut
from app.auth.jwt_handler import get_current_active_user
from app.services.email_service import send_subscription_reminder

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/", response_model=SubscriptionOut)
def create_subscription(sub_in: SubscriptionCreate, db: Session = Depends(get_db), bg: BackgroundTasks = None, user: User = Depends(get_current_active_user)):
    product = db.query(Product).filter(Product.id == sub_in.product_id).first()
    pet = db.query(Pet).filter(Pet.id == sub_in.pet_id, Pet.user_id == user.id).first()
    if not product or not pet:
        raise HTTPException(status_code=400, detail="Invalid product or pet")
    next_date = date.today() + (timedelta(days=7) if sub_in.cadence == "weekly" else timedelta(days=30))
    sub = Subscription(
        user_id=user.id,
        pet_id=pet.id,
        product_id=product.id,
        quantity=sub_in.quantity,
        cadence=sub_in.cadence,
        next_delivery_date=next_date,
        status=SubscriptionStatus.active,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    if bg:
        bg.add_task(send_subscription_reminder, user.email, sub.id, next_date)
    return sub


@router.get("/", response_model=list[SubscriptionOut])
def list_subscriptions(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    return db.query(Subscription).filter(Subscription.user_id == user.id).order_by(Subscription.next_delivery_date.asc()).all()


@router.patch("/{sub_id}", response_model=SubscriptionOut)
def update_subscription(sub_id: int, sub_in: SubscriptionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.user_id == user.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    for k, v in sub_in.model_dump(exclude_unset=True).items():
        setattr(sub, k, v)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.delete("/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.user_id == user.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(sub)
    db.commit()
    return {"detail": "Subscription cancelled"}


@router.post("/{sub_id}/renew")
def renew_subscription(sub_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    sub = db.query(Subscription).filter(Subscription.id == sub_id, Subscription.user_id == user.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub.status != SubscriptionStatus.active:
        raise HTTPException(status_code=400, detail="Subscription is not active")
    product = db.query(Product).filter(Product.id == sub.product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail="Product not found")
    total_amount = product.price * sub.quantity
    order = Order(
        user_id=user.id,
        total_amount=total_amount,
        discount=0.0,
        status=OrderStatus.pending,
        shipping_address=None,
        payment_status=PaymentStatus.unpaid,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    item = OrderItem(order_id=order.id, product_id=product.id, quantity=sub.quantity, unit_price=product.price)
    db.add(item)
    # advance next delivery date by cadence
    next_date = date.today() + (timedelta(days=7) if sub.cadence == "weekly" else timedelta(days=30))
    sub.next_delivery_date = next_date
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"order_id": order.id, "next_delivery_date": str(next_date)}