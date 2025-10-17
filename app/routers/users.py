from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserOut, UserUpdate
from app.auth.jwt_handler import get_current_active_user, get_current_admin

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if update.full_name is not None:
        current_user.full_name = update.full_name
    if update.is_active is not None:
        current_user.is_active = update.is_active
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}