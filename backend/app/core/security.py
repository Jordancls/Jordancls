from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from jose import jwt
from passlib.context import CryptContext
from fastapi import Response
from app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, minutes: int | None = None) -> str:
    expire_minutes = minutes or settings.access_token_expire_minutes
    to_encode: Dict[str, Any] = {"sub": subject, "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=expire_minutes)}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def create_refresh_token(subject: str, days: int | None = None) -> str:
    expire_days = days or settings.refresh_token_expire_days
    to_encode: Dict[str, Any] = {"sub": subject, "exp": datetime.now(tz=timezone.utc) + timedelta(days=expire_days), "type": "refresh"}
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


REFRESH_COOKIE_NAME = "sg_refresh"


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/api/v1/auth",
        max_age=int(timedelta(days=settings.refresh_token_expire_days).total_seconds()),
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/auth")
