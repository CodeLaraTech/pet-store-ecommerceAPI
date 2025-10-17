from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy import Enum, ForeignKey, String, Text, Float, Integer, Boolean, DateTime
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str):
    admin = "admin"
    customer = "customer"


class OrderStatus(str):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"
    shipped = "shipped"
    delivered = "delivered"


class PaymentStatus(str):
    unpaid = "unpaid"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"


class SubscriptionStatus(str):
    active = "active"
    paused = "paused"
    cancelled = "cancelled"


class Cadence(str):
    weekly = "weekly"
    monthly = "monthly"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=UserRole.customer, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pets: Mapped[List["Pet"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="user")
    reviews: Mapped[List["Review"]] = relationship(back_populates="user")


class Pet(Base):
    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    species: Mapped[str] = mapped_column(String(64))
    breed: Mapped[Optional[str]] = mapped_column(String(120))
    age: Mapped[Optional[int]] = mapped_column(Integer)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    allergies: Mapped[Optional[List[str]]] = mapped_column(JSON)
    preferred_ingredients: Mapped[Optional[List[str]]] = mapped_column(JSON)
    activity_level: Mapped[Optional[str]] = mapped_column(String(64))
    health_conditions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    photo_url: Mapped[Optional[str]] = mapped_column(String(255))

    owner: Mapped[User] = relationship(back_populates="pets")
    subscriptions: Mapped[List["Subscription"]] = relationship(back_populates="pet")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    species_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    ingredients: Mapped[Optional[str]] = mapped_column(Text)
    nutritional_info: Mapped[Optional[dict]] = mapped_column(JSON)
    allergens: Mapped[Optional[List[str]]] = mapped_column(JSON)
    recommended_age: Mapped[Optional[int]] = mapped_column(Integer)
    portion_size: Mapped[Optional[float]] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float, index=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    subscription_available: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    feeding_guidelines: Mapped[Optional[str]] = mapped_column(Text)
    storage_instructions: Mapped[Optional[str]] = mapped_column(Text)
    images: Mapped[Optional[List[str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")
    reviews: Mapped[List["Review"]] = relationship(back_populates="product")


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(16))  # percent|fixed
    discount_value: Mapped[float] = mapped_column(Float)
    valid_from: Mapped[Optional[date]] = mapped_column()
    valid_to: Mapped[Optional[date]] = mapped_column()
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    applicable_products: Mapped[Optional[List[int]]] = mapped_column(JSON)
    new_user_only: Mapped[bool] = mapped_column(Boolean, default=False)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    total_amount: Mapped[float] = mapped_column(Float)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default=OrderStatus.pending, index=True)
    shipping_address: Mapped[Optional[dict]] = mapped_column(JSON)
    payment_status: Mapped[str] = mapped_column(String(32), default=PaymentStatus.unpaid)
    tracking_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="order_items")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    cadence: Mapped[str] = mapped_column(String(32), default=Cadence.monthly)
    next_delivery_date: Mapped[Optional[date]] = mapped_column()
    status: Mapped[str] = mapped_column(String(32), default=SubscriptionStatus.active, index=True)
    trial_ends_at: Mapped[Optional[date]] = mapped_column()
    billing_method: Mapped[Optional[str]] = mapped_column(String(32))
    last_payment_status: Mapped[Optional[str]] = mapped_column(String(32))

    user: Mapped[User] = relationship(back_populates="subscriptions")
    pet: Mapped[Pet] = relationship(back_populates="subscriptions")
    product: Mapped[Product] = relationship()


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    product: Mapped[Product] = relationship(back_populates="reviews")
    user: Mapped[User] = relationship(back_populates="reviews")