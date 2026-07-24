"""Forecast endpoints: run, list, compare, seasonal (auth required)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from .. import models, schemas
from ..auth import get_current_user
from ..config import settings
from ..services.forecast_service import run_forecast, compare_models
from ..utils.seasonal import analyze_seasonality


router = APIRouter(prefix="/forecast", tags=["forecast"])


# Rate-limit expensive LSTM training
def _limiter(request: Request) -> Limiter:
    return request.app.state.limiter


@router.post("/run", response_model=schemas.ForecastOut)
def run(
    payload: schemas.ForecastRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    try:
        return run_forecast(db, payload.product_id, payload.model_name, payload.horizon_days)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except (ImportError, RuntimeError) as e:                # model not installed
        raise HTTPException(503, str(e))
    except Exception as e:
        raise HTTPException(500, f"Forecast failed: {e}")


@router.post("/compare")
def compare(
    payload: schemas.ForecastRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Run all 3 models and return comparison.  Heavy — admin/analyst only."""
    if user.role == "viewer":
        raise HTTPException(403, "Compare is restricted to admin/analyst")
    try:
        return compare_models(db, payload.product_id, payload.horizon_days)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/history/{product_id}")
def get_history(
    product_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    rows = (
        db.query(models.Forecast)
        .filter(models.Forecast.product_id == product_id)
        .order_by(models.Forecast.model_name, models.Forecast.forecast_date.asc())
        .all()
    )
    by_model: dict = {}
    for r in rows:
        by_model.setdefault(r.model_name, {
            "metrics": {"mae": r.mae, "rmse": r.rmse, "mape": r.mape},
            "horizon_days": r.horizon_days,
            "points": [],
        })
        by_model[r.model_name]["points"].append({
            "forecast_date": str(r.forecast_date),
            "predicted_quantity": r.predicted_quantity,
            "lower_bound": r.lower_bound,
            "upper_bound": r.upper_bound,
        })
    return {"product_id": product_id, "by_model": by_model}


@router.get("/seasonal/{product_id}")
def get_seasonal(
    product_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    sales = (
        db.query(models.Sale)
        .filter(models.Sale.product_id == product_id)
        .order_by(models.Sale.sale_date.asc())
        .all()
    )
    dates = [s.sale_date for s in sales]
    qtys = [float(s.quantity) for s in sales]
    return analyze_seasonality(dates, qtys)


@router.get("/models")
def list_models(_: models.User = Depends(get_current_user)):
    return {
        "models": [
            {"name": "prophet", "description": "Facebook Prophet - additive model with trend + seasonality"},
            {"name": "xgboost", "description": "Gradient boosted trees with engineered lag/rolling features"},
            {"name": "lstm", "description": "Deep learning LSTM for non-linear temporal patterns"},
        ]
    }
