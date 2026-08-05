"""Centralised application settings loaded from environment variables.

All runtime knobs live here.  Anything sensitive (DB password, JWT secret)
must be supplied via `.env` (see `.env.example`).
"""
from __future__ import annotations
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict



PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = DATA_DIR / "reports"
MODELS_DIR = DATA_DIR / "models"


class Settings(BaseSettings):
    # ---- General ----
    APP_NAME: str = "Retail Demand Forecasting System"
    APP_VERSION: str = "1.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ---- Database ----
    DATABASE_URL: str = f"sqlite:///{(DATA_DIR / 'retail_forecast.db').as_posix()}"
    DB_ECHO: bool = False

    # ---- Auth / Security ----
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(64),
        description="JWT signing key.  Set a strong value in production via .env",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8            # 8 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7      # 7 days
    BCRYPT_ROUNDS: int = 12

    # ---- CORS ----
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ---- Rate limiting (slowapi) ----
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_FORECAST: str = "10/minute"     # LSTM is expensive
    RATE_LIMIT_AUTH: str = "10/minute"         # brute-force protection

    # ---- Forecasting defaults ----
    FORECAST_HORIZON_DAYS: int = 30
    PROPHET_INTERVAL_WIDTH: float = 0.95
    XGB_N_ESTIMATORS: int = 500
    LSTM_EPOCHS: int = 20
    LSTM_SEQUENCE_LENGTH: int = 30

    # ---- Inventory defaults ----
    SAFETY_STOCK_DAYS: int = 7
    REORDER_LEAD_DAYS: int = 5
    SAFETY_STOCK_Z: float = 1.65   # 95% service level

    # ---- Upload limits (security) ----
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024   # 10 MB
    MAX_CSV_ROWS: int = 200_000

    # ---- Sample data path (used by generate_sample_csv.py) ----
    SAMPLE_DATA_PATH: Path = DATA_DIR / "sample_sales.csv"

    # ---- Pydantic-settings config ----
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        """Allow CORS_ORIGINS to be supplied as a JSON array or comma-separated string."""
        if isinstance(v, str) and not v.startswith("["):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        """Ensure SQLite file paths use forward slashes on Windows to avoid escape issues."""
        if isinstance(v, str) and v.startswith("sqlite"):
            return v.replace("\\", "/")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()


# Convenience alias for `from .config import settings`
settings = get_settings()
