"""Authentication endpoints: register, login, refresh, me."""
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from .. import models, schemas
from ..auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user,
)
from ..config import settings


router = APIRouter(prefix="/auth", tags=["auth"])

# A local limiter is wired in main.py; here we just declare the decorator.
# (slowapi uses the limiter attached to `app.state.limiter`.)
def _limiter(request: Request):
    return request.app.state.limiter


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Self-registration is enabled for analyst/viewer roles by default.
    Admin accounts can only be created by another admin.
    """
    if payload.role == "admin":
        # Block self-registration as admin
        existing_admins = (
            db.query(models.User).filter(models.User.role == "admin").count()
        )
        # Allow first admin bootstrap (no admins exist)
        if existing_admins > 0:
            raise HTTPException(403, "Admin accounts can only be created by an existing admin")
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(409, "Username already taken")
    if payload.email and db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(409, "Email already in use")
    user = models.User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "User could not be created")
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password flow — returns JWT access + refresh tokens."""
    user = db.query(models.User).filter(models.User.username == form.username).first()
    # Generic message to prevent user enumeration
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user or not verify_password(form.password, user.hashed_password):
        raise invalid
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return schemas.TokenOut(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=schemas.TokenOut)
def refresh(refresh_token: str, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Not a refresh token")
    user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or disabled")
    return schemas.TokenOut(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=schemas.UserOut.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the password of the currently-authenticated user."""
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(400, "Old password is incorrect")
    # Re-use validator
    try:
        schemas.UserCreate(username=user.username, password=new_password)
    except Exception as e:
        raise HTTPException(422, f"New password too weak: {e}")
    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"message": "Password updated"}
