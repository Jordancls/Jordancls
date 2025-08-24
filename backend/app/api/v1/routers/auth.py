from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.db.session import get_db
from app.db.models import User
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    set_refresh_cookie,
    clear_refresh_cookie,
    REFRESH_COOKIE_NAME,
)
from app.core.config import settings


router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/seed-admin", response_model=TokenResponse)
def seed_admin(response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == "admin@sg.com").first()
    if not user:
        user = User(
            email="admin@sg.com",
            hashed_password=get_password_hash("admin123"),
            role="ADMIN",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, role=user.role, email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password) or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, role=user.role, email=user.email)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    access = create_access_token(user.email)
    refresh = create_refresh_token(user.email)
    set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access, role=user.role, email=user.email)


@router.post("/logout")
def logout(response: Response):
    clear_refresh_cookie(response)
    return {"detail": "Logged out"}
