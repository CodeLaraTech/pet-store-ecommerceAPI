from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserOut
from app.auth.jwt_handler import (
    get_password_hash,
    authenticate_user,
    create_access_token,
)
from app.services.email_service import send_welcome_email

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db), bg: BackgroundTasks = None):
    exists = db.query(User).filter(User.email == user_in.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_in.email, full_name=user_in.full_name, hashed_password=get_password_hash(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    if bg:
        bg.add_task(send_welcome_email, user.email, user.full_name or user.email)
    return user


@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_in.email, login_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token({"sub": user.email}, expires_delta=timedelta(minutes=60))
    return Token(access_token=token)