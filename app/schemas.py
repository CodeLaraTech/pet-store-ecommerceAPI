from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "email": "jane@example.com",
                "full_name": "Jane Doe",
                "password": "strongpassword123"
            }]
        }
    }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PetBase(BaseModel):
    name: str
    species: str
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    allergies: Optional[List[str]] = None
    preferred_ingredients: Optional[List[str]] = None
    activity_level: Optional[str] = None
    health_conditions: Optional[List[str]] = None
    photo_url: Optional[str] = None


class PetCreate(PetBase):
    pass


class PetUpdate(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    allergies: Optional[List[str]] = None
    preferred_ingredients: Optional[List[str]] = None
    activity_level: Optional[str] = None
    health_conditions: Optional[List[str]] = None
    photo_url: Optional[str] = None


class PetOut(PetBase):
    id: int
    user_id: int
    portion_suggestion: Optional[dict] = None

    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    name: str
    slug: str
    species_tags: Optional[List[str]] = None
    ingredients: Optional[str] = None
    nutritional_info: Optional[dict] = None
    allergens: Optional[List[str]] = None
    recommended_age: Optional[int] = None
    portion_size: Optional[float] = None
    price: float
    stock: int = 0
    subscription_available: bool = False
    feeding_guidelines: Optional[str] = None
    storage_instructions: Optional[str] = None
    images: Optional[List[str]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    subscription_available: Optional[bool] = None
    feeding_guidelines: Optional[str] = None
    storage_instructions: Optional[str] = None
    images: Optional[List[str]] = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: Optional[dict] = None
    coupon_code: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderOut(BaseModel):
    id: int
    user_id: int
    total_amount: float
    discount: float
    status: str
    payment_status: str
    shipping_address: Optional[dict]
    tracking_id: Optional[str]
    created_at: datetime
    items: List[dict]

    model_config = {"from_attributes": True}


class SubscriptionCreate(BaseModel):
    pet_id: int
    product_id: int
    quantity: int = Field(gt=0)
    cadence: str = "monthly"


class SubscriptionUpdate(BaseModel):
    quantity: Optional[int] = None
    cadence: Optional[str] = None
    status: Optional[str] = None


class SubscriptionOut(BaseModel):
    id: int
    user_id: int
    pet_id: int
    product_id: int
    quantity: int
    cadence: str
    next_delivery_date: Optional[date]
    status: str

    model_config = {"from_attributes": True}


class CouponCreate(BaseModel):
    code: str
    discount_type: str
    discount_value: float
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    max_uses: Optional[int] = None
    applicable_products: Optional[List[int]] = None
    new_user_only: bool = False


class CouponApplyRequest(BaseModel):
    code: str
    amount: float
    product_ids: Optional[List[int]] = None


class CouponValidationResponse(BaseModel):
    code: str
    valid: bool
    discount_value: Optional[float] = None
    discount_type: Optional[str] = None


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    comment: Optional[str]
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}