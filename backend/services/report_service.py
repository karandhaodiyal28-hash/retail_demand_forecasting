"""Report generation: forecast / inventory / seasonal in JSON or CSV."""
from __future__ import annotations
import csv
import json
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from sqlalchemy.orm import Session

from .. import models
from ..config import settings, REPORTS_DIR
from .inventory_service import get_all_inventory_status
from ..utils.seasonal import analyze_seasonality


def _new_report_row(db: Session, *, rtype: str, product_id, fmt: str, params: str, file_path: Path, user_id: int | None) -> models.Report:
    row = models.Report(
        report_type=rtype, product_id=product_id, params=params,
        file_path=str(file_path), format=fmt, created_by=user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def generate_forecast_report(db: Session, product_id: int, fmt: str = "json", user_id: int | None = None) -> Dict:
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise ValueError(f"Product {product_id} not found")
    rows = (
        db.query(models.Forecast)
        .filter(models.Forecast.product_id == product_id)
        .order_by(models.Forecast.model_name, models.Forecast.forecast_date.asc())
        .all()
    )
    payload = {
        "report_type": "forecast",
        "product": {"id": p.id, "sku": p.sku, "name": p.name},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "models": {},
    }
    for r in rows:
        payload["models"].setdefault(r.model_name, {
            "metrics": {"mae": r.mae, "rmse": r.rmse, "mape": r.mape},
            "horizon_days": r.horizon_days,
            "points": [],
        })
        payload["models"][r.model_name]["points"].append({
            "forecast_date": r.forecast_date.isoformat(),
            "predicted_quantity": r.predicted_quantity,
            "lower_bound": r.lower_bound,
            "upper_bound": r.upper_bound,
        })

    fname = f"forecast_{p.sku}_{datetime.utcnow():%Y%m%d_%H%M%S}.{fmt}"
    fpath = REPORTS_DIR / fname
    if fmt == "json":
        fpath.write_text(json.dumps(payload, indent=2, default=str))
    else:
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["model", "forecast_date", "predicted_quantity", "lower_bound", "upper_bound"])
            for model_name, m in payload["models"].items():
                for pt in m["points"]:
                    w.writerow([model_name, pt["forecast_date"], pt["predicted_quantity"], pt["lower_bound"], pt["upper_bound"]])
    rep = _new_report_row(db, rtype="forecast", product_id=product_id, fmt=fmt,
                          params=json.dumps({"product_id": product_id}), file_path=fpath, user_id=user_id)
    return {"report_id": rep.id, "format": fmt, "file_path": str(fpath), "size_bytes": fpath.stat().st_size}


def generate_inventory_report(db: Session, fmt: str = "json", user_id: int | None = None) -> Dict:
    rows = get_all_inventory_status(db)
    payload = {
        "report_type": "inventory",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "rows": rows,
    }
    fname = f"inventory_{datetime.utcnow():%Y%m%d_%H%M%S}.{fmt}"
    fpath = REPORTS_DIR / fname
    if fmt == "json":
        fpath.write_text(json.dumps(payload, indent=2, default=str))
    else:
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["sku", "name", "current_stock", "reorder_point", "safety_stock",
                        "recommended_order_qty", "status", "lead_time_days", "avg_daily_demand"])
            for r in rows:
                w.writerow([r["sku"], r["name"], r["current_stock"], r["reorder_point"],
                            r["safety_stock"], r["recommended_order_qty"], r["status"],
                            r["lead_time_days"], r["avg_daily_demand"]])
    rep = _new_report_row(db, rtype="inventory", product_id=None, fmt=fmt,
                          params=json.dumps({}), file_path=fpath, user_id=user_id)
    return {"report_id": rep.id, "format": fmt, "file_path": str(fpath), "size_bytes": fpath.stat().st_size}


def generate_seasonal_report(db: Session, product_id: int, fmt: str = "json", user_id: int | None = None) -> Dict:
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise ValueError(f"Product {product_id} not found")
    sales = (
        db.query(models.Sale)
        .filter(models.Sale.product_id == product_id)
        .order_by(models.Sale.sale_date.asc())
        .all()
    )
    analysis = analyze_seasonality([s.sale_date for s in sales], [float(s.quantity) for s in sales])
    payload = {
        "report_type": "seasonal",
        "product": {"id": p.id, "sku": p.sku, "name": p.name},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "analysis": analysis,
    }
    fname = f"seasonal_{p.sku}_{datetime.utcnow():%Y%m%d_%H%M%S}.{fmt}"
    fpath = REPORTS_DIR / fname
    if fmt == "json":
        fpath.write_text(json.dumps(payload, indent=2, default=str))
    else:
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["key", "value"])
            w.writerow(["trend_direction", analysis.get("trend_direction")])
            w.writerow(["trend_slope_per_day", analysis.get("trend_slope_per_day")])
            w.writerow(["peak_weekday", analysis.get("peak_weekday")])
            w.writerow(["peak_month", analysis.get("peak_month")])
            w.writerow(["avg_daily", analysis.get("avg_daily")])
            w.writerow(["max_daily", analysis.get("max_daily")])
            w.writerow(["min_daily", analysis.get("min_daily")])
            w.writerow(["std_daily", analysis.get("std_daily")])
            w.writerow([])
            w.writerow(["weekday", "avg_quantity"])
            for k, v in (analysis.get("weekly_pattern") or {}).items():
                w.writerow([k, v])
            w.writerow([])
            w.writerow(["month", "avg_quantity"])
            for k, v in (analysis.get("monthly_pattern") or {}).items():
                w.writerow([k, v])
    rep = _new_report_row(db, rtype="seasonal", product_id=product_id, fmt=fmt,
                          params=json.dumps({"product_id": product_id}), file_path=fpath, user_id=user_id)
    return {"report_id": rep.id, "format": fmt, "file_path": str(fpath), "size_bytes": fpath.stat().st_size}
