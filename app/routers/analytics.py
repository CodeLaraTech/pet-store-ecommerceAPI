from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth.jwt_handler import get_current_admin
from app.services.analytics_service import (
    get_overview,
    revenue_series,
    top_products,
    species_trends,
    subscription_churn,
)

router = APIRouter(prefix="/admin/analytics", tags=["Analytics"]) 


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return get_overview(db)


@router.get("/revenue")
def revenue(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return revenue_series(db)


@router.get("/top-products")
def top_products_view(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return top_products(db)


@router.get("/species-trends")
def species_trends_view(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return species_trends(db)


@router.get("/subscription-churn")
def subscription_churn_view(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return subscription_churn(db)