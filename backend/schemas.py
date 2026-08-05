"""Pydantic schemas for request validation and response shaping.

All API boundary types live here.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
import re


# ------------------- Auth / User -------------------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(default=None, max_length=128)
    role: str = Field(default="analyst")

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_.-]+$", v):
            raise ValueError("username may only contain letters, numbers, '_', '.', '-'")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("password must contain at least one letter and one digit")
        return v

    @field_validator("role")
    @classmethod
    def _validate_role(cls, v: str) -> str:
        if v not in {"admin", "analyst", "viewer"}:
            raise ValueError("role must be one of: admin, analyst, viewer")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: Optional[str]
    role: str
    is_active: int
    created_at: datetime
    last_login_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class TokenOut(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


# ------------------- Product / Sale / Forecast / Inventory / Report -------------------

class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    category: Optional[str] = Field(default=None, max_length=128)
    unit_cost: float = Field(default=0, ge=0)
    unit_price: float = Field(default=0, ge=0)
    lead_time_days: int = Field(default=5, ge=0, le=365)

    @field_validator("sku")
    @classmethod
    def _validate_sku(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9._-]+$", v):
            raise ValueError("sku may only contain letters, numbers, '.', '_', '-'")
        return v


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=256)
    category: Optional[str] = Field(default=None, max_length=128)
    unit_cost: Optional[float] = Field(default=None, ge=0)
    unit_price: Optional[float] = Field(default=None, ge=0)
    lead_time_days: Optional[int] = Field(default=None, ge=0, le=365)


class ProductOut(ProductBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SaleCreate(BaseModel):
    product_id: int = Field(ge=1)
    sale_date: date
    quantity: float = Field(ge=0)
    revenue: float = Field(default=0, ge=0)


class SaleOut(BaseModel):
    id: int
    product_id: int
    sale_date: date
    quantity: float
    revenue: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class SalesBulkIn(BaseModel):
    sales: List[SaleCreate]


class ForecastRequest(BaseModel):
    product_id: int = Field(ge=1)
    model_name: str = Field(pattern=r"^(prophet|xgboost|lstm)$")
    horizon_days: int = Field(default=30, ge=1, le=365)

    model_config = ConfigDict(protected_namespaces=())


class ForecastOut(BaseModel):
    product_id: int
    model_name: str
    horizon_days: int
    metrics: Dict[str, float]
    forecasts: List[Dict[str, Any]]

    model_config = ConfigDict(protected_namespaces=())


class InventoryUpdate(BaseModel):
    current_stock: float = Field(ge=0)


class InventoryOut(BaseModel):
    product_id: int
    sku: str
    name: str
    current_stock: float
    reorder_point: float
    safety_stock: float
    recommended_order_qty: float
    status: str
    notes: Optional[str] = None
    lead_time_days: int
    avg_daily_demand: float


class ReportRequest(BaseModel):
    report_type: str = Field(pattern=r"^(forecast|inventory|seasonal)$")
    product_id: Optional[int] = Field(default=None, ge=1)
    format: str = Field(default="json", pattern=r"^(json|csv)$")


class MessageOut(BaseModel):
    message: str
    detail: Optional[str] = None
