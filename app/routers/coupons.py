from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Coupon, User
from app.schemas import CouponCreate, CouponApplyRequest, CouponValidationResponse
from app.auth.jwt_handler import get_current_admin, get_current_active_user

router = APIRouter(prefix="/coupons", tags=["Coupons"]) 


@router.post("/", response_model=dict)
def create_coupon(c_in: CouponCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    exists = db.query(Coupon).filter(Coupon.code == c_in.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="Code already exists")
    c = Coupon(**c_in.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "code": c.code}


@router.get("/validate/{code}", response_model=CouponValidationResponse)
def validate_coupon(code: str, db: Session = Depends(get_db)):
    c = db.query(Coupon).filter(Coupon.code == code).first()
    return CouponValidationResponse(code=code, valid=bool(c), discount_value=(c.discount_value if c else None), discount_type=(c.discount_type if c else None))


@router.post("/apply")
def apply_coupon(req: CouponApplyRequest, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    c = db.query(Coupon).filter(Coupon.code == req.code).first()
    if not c:
        raise HTTPException(status_code=404, detail="Coupon not found")
    today = c.valid_from or c.valid_to
    if c.valid_from and today < c.valid_from:
        raise HTTPException(status_code=400, detail="Coupon not yet valid")
    if c.valid_to and today > c.valid_to:
        raise HTTPException(status_code=400, detail="Coupon expired")
    if c.max_uses and c.used_count >= c.max_uses:
        raise HTTPException(status_code=400, detail="Coupon usage exceeded")
    if c.applicable_products and req.product_ids:
        if not any(pid in c.applicable_products for pid in req.product_ids):
            raise HTTPException(status_code=400, detail="Coupon not applicable to products")
    discount = req.amount * (c.discount_value / 100.0) if c.discount_type == "percent" else c.discount_value
    c.used_count += 1
    db.add(c)
    db.commit()
    return {"discount": float(min(discount, req.amount))}