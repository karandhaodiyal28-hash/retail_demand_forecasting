"""Authentication & authorisation helpers.

* bcrypt password hashing
* JWT access + refresh tokens
* FastAPI dependency `get_current_user` to protect endpoints
* Role-based dependency `require_role`
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from . import models

# bcrypt work factor comes from settings (default 12)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login", auto_error=True)

ACCESS_TOKEN_TY = "access"
REFRESH_TOKEN_TY = "refresh"


# ------------- password helpers -------------

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time verification via passlib."""
    return pwd_context.verify(plain, hashed)


# ------------- JWT helpers -------------

def _create_token(subject: str, token_type: str, expires_minutes: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user: models.User) -> str:
    return _create_token(str(user.id), ACCESS_TOKEN_TY, settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(user: models.User) -> str:
    return _create_token(str(user.id), REFRESH_TOKEN_TY, settings.REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT.  Raises HTTPException on failure."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ------------- FastAPI dependencies -------------

def _user_from_token(token: str, db: Session) -> models.User:
    payload = decode_token(token)
    if payload.get("type") != ACCESS_TOKEN_TY:
        raise HTTPException(401, "Wrong token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token missing subject")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or disabled")
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Standard `Depends` for protected endpoints."""
    return _user_from_token(token, db)


def get_current_active_admin(
    user: models.User = Depends(get_current_user),
) -> models.User:
    """Restrict an endpoint to admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


def require_role(*roles: str):
    """Factory: returns a dependency that allows only the given roles."""
    allowed = set(roles)

    def _dep(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Required role(s): {', '.join(sorted(allowed))}",
            )
        return user

    return _dep
