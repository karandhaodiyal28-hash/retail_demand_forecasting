"""SQLAlchemy ORM models for the retail forecasting system.

All tables are kept in this single file for clarity and easy review.
"""
from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey,
    Text, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """Application user (used by /auth/login)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(256), unique=True, nullable=True, index=True)
    full_name = Column(String(128), nullable=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default="analyst")  # admin | analyst | viewer
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(256), nullable=False)
    category = Column(String(128), index=True)
    unit_cost = Column(Float, default=0)
    unit_price = Column(Float, default=0)
    lead_time_days = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sales = relationship("Sale", back_populates="product", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="product", cascade="all, delete-orphan")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    quantity = Column(Float, default=0)
    revenue = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="sales")

    __table_args__ = (
        Index("idx_sales_product_date", "product_id", "sale_date"),
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(64), nullable=False)
    forecast_date = Column(Date, nullable=False)
    predicted_quantity = Column(Float, default=0)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    horizon_days = Column(Integer, default=30)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    mape = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="forecasts")

    __table_args__ = (
        Index("idx_forecasts_product_model_date", "product_id", "model_name", "forecast_date"),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_stock = Column(Float, default=0)
    reorder_point = Column(Float, default=0)
    safety_stock = Column(Float, default=0)
    recommended_order_qty = Column(Float, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    product = relationship("Product", back_populates="inventory")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    report_type = Column(String(64), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    params = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    format = Column(String(16), default="json")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
