"""Database setup using SQLAlchemy ORM.

Works with SQLite (default, zero-config) and PostgreSQL (set DATABASE_URL).
"""
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings


# SQLite needs check_same_thread=False for FastAPI's threaded request handling.
_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (idempotent)."""
    # Import models so they're registered with Base.metadata
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
