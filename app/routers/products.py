from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Review, User
from app.schemas import ProductCreate, ProductUpdate, ProductOut, ReviewCreate, ReviewOut
from app.auth.jwt_handler import get_current_active_user, get_current_admin

router = APIRouter(prefix="/products", tags=["Products"]) 


@router.post("/", response_model=ProductOut)
def create_product(prod_in: ProductCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    exists = db.query(Product).filter(Product.slug == prod_in.slug).first()
    if exists:
        raise HTTPException(status_code=400, detail="Slug already exists")
    product = Product(**prod_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/", response_model=List[ProductOut])
def list_products(
    db: Session = Depends(get_db),
    species: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    subscription_available: Optional[bool] = None,
    sort_by: Optional[str] = "created_at",
    order: Optional[str] = "desc",
    page: int = 1,
    page_size: int = 20,
):
    q = db.query(Product)
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if subscription_available is not None:
        q = q.filter(Product.subscription_available == subscription_available)
    if sort_by in {"price", "created_at", "updated_at", "stock"}:
        col = getattr(Product, sort_by)
        q = q.order_by(col.desc() if order == "desc" else col.asc())
    else:
        q = q.order_by(Product.created_at.desc())

    # Fetch and apply species filter in Python for cross-dialect safety
    items = q.all()
    if species:
        items = [p for p in items if p.species_tags and species in p.species_tags]

    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, prod_in: ProductUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in prod_in.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}


@router.post("/{product_id}/reviews", response_model=ReviewOut)
def create_review(product_id: int, review_in: ReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    review = Review(product_id=product.id, user_id=user.id, **review_in.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{product_id}/reviews", response_model=List[ReviewOut])
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.product_id == product_id, Review.is_approved == True).order_by(Review.created_at.desc()).all()


@router.patch("/reviews/{review_id}/approve")
def approve_review(review_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_approved = True
    db.add(review)
    db.commit()
    return {"detail": "Review approved"}