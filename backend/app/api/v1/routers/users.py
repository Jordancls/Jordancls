from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.api.v1.deps import require_roles
from app.db.session import get_db
from app.db.models import User
from app.core.security import get_password_hash


router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserPatch(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.post("/", response_model=UserOut, dependencies=[Depends(require_roles("ADMIN"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role not in ("ADMIN", "SUPERVISOR", "USER"):
        raise HTTPException(status_code=400, detail="Invalid role")
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=get_password_hash(payload.password), role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/", response_model=list[UserOut], dependencies=[Depends(require_roles("ADMIN"))])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles("ADMIN"))])
def patch_user(user_id: int, payload: UserPatch, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role:
        if payload.role not in ("ADMIN", "SUPERVISOR", "USER"):
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", dependencies=[Depends(require_roles("ADMIN"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"detail": "User deactivated"}
