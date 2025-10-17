from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Pet, User
from app.schemas import PetCreate, PetUpdate, PetOut
from app.auth.jwt_handler import get_current_active_user
from app.utils import suggest_portion_and_meal

router = APIRouter(prefix="/pets", tags=["Pets"])


@router.post("/", response_model=PetOut)
def create_pet(pet_in: PetCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    pet = Pet(user_id=current_user.id, **pet_in.model_dump())
    db.add(pet)
    db.commit()
    db.refresh(pet)
    out = PetOut.model_validate(pet)
    out.portion_suggestion = suggest_portion_and_meal(pet.weight, pet.activity_level)
    return out


@router.get("/", response_model=list[PetOut])
def list_pets(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    pets = db.query(Pet).filter(Pet.user_id == current_user.id).all()
    outs = []
    for p in pets:
        out = PetOut.model_validate(p)
        out.portion_suggestion = suggest_portion_and_meal(p.weight, p.activity_level)
        outs.append(out)
    return outs


@router.get("/{pet_id}", response_model=PetOut)
def get_pet(pet_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet or (pet.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Pet not found")
    out = PetOut.model_validate(pet)
    out.portion_suggestion = suggest_portion_and_meal(pet.weight, pet.activity_level)
    return out


@router.put("/{pet_id}", response_model=PetOut)
def update_pet(pet_id: int, pet_in: PetUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet or (pet.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Pet not found")
    for k, v in pet_in.model_dump(exclude_unset=True).items():
        setattr(pet, k, v)
    db.add(pet)
    db.commit()
    db.refresh(pet)
    out = PetOut.model_validate(pet)
    out.portion_suggestion = suggest_portion_and_meal(pet.weight, pet.activity_level)
    return out


@router.delete("/{pet_id}")
def delete_pet(pet_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet or (pet.user_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=404, detail="Pet not found")
    db.delete(pet)
    db.commit()
    return {"detail": "Pet deleted"}