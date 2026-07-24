"""Forecast orchestration: route to right model, persist results, compare models."""
from __future__ import annotations
from typing import Dict
from sqlalchemy.orm import Session
import pandas as pd

from .. import models
from ..config import settings
from . import prophet_service, xgboost_service, lstm_service


MODEL_REGISTRY = {
    "prophet": prophet_service,
    "xgboost": xgboost_service,
    "lstm":     lstm_service,
}


def _load_series(db: Session, product_id: int):
    rows = (
        db.query(models.Sale)
        .filter(models.Sale.product_id == product_id)
        .order_by(models.Sale.sale_date.asc())
        .all()
    )
    if not rows:
        raise ValueError("No sales history for this product")
    return [r.sale_date for r in rows], [float(r.quantity) for r in rows]


def run_forecast(db: Session, product_id: int, model_name: str, horizon_days: int) -> Dict:
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{model_name}'.  Choose from {list(MODEL_REGISTRY)}")
    if not db.query(models.Product).filter(models.Product.id == product_id).first():
        raise ValueError(f"Product {product_id} not found")

    dates, qtys = _load_series(db, product_id)
    service = MODEL_REGISTRY[model_name]
    forecasts, metrics = service.fit_predict(dates, qtys, horizon_days)

    # Persist to DB (replace any prior forecasts for this product+model within the same horizon)
    db.query(models.Forecast).filter(
        models.Forecast.product_id == product_id,
        models.Forecast.model_name == model_name,
    ).delete()
    for f in forecasts:
        db.add(models.Forecast(
            product_id=product_id,
            model_name=model_name,
            forecast_date=pd.to_datetime(f["forecast_date"]).date(),
            predicted_quantity=f["predicted_quantity"],
            lower_bound=f["lower_bound"],
            upper_bound=f["upper_bound"],
            horizon_days=horizon_days,
            mae=metrics["mae"],
            rmse=metrics["rmse"],
            mape=metrics["mape"],
        ))
    db.commit()

    total_pred = round(sum(f["predicted_quantity"] for f in forecasts), 2)
    return {
        "product_id": product_id,
        "model_name": model_name,
        "horizon_days": horizon_days,
        "metrics": metrics,
        "total_predicted": total_pred,
        "forecasts": forecasts,
    }


def compare_models(db: Session, product_id: int, horizon_days: int) -> Dict:
    results: Dict[str, Dict] = {}
    best_model, best_rmse = None, float("inf")
    for name in MODEL_REGISTRY:
        try:
            res = run_forecast(db, product_id, name, horizon_days)
            results[name] = {
                "metrics": res["metrics"],
                "total_predicted": res["total_predicted"],
            }
            rmse = res["metrics"].get("rmse", float("inf"))
            if rmse < best_rmse:
                best_rmse, best_model = rmse, name
        except Exception as e:
            results[name] = {"error": str(e)}
    return {
        "product_id": product_id,
        "horizon_days": horizon_days,
        "results": results,
        "best_model": best_model,
    }
