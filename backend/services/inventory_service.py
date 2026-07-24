"""Inventory optimisation service.

Computes reorder points, safety stock, recommended order quantities, and a
status flag (OK / LOW / REORDER / OVERSTOCK) for every product.
"""
from __future__ import annotations
import math
from datetime import date, timedelta
from typing import List, Dict
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from .. import models
from ..config import settings


def _daily_stats(dates, qtys):
    if not qtys:
        return 0.0, 0.0
    s = pd.Series(qtys, index=pd.to_datetime(dates))
    s = s.groupby(s.index.date).sum()
    return float(s.mean()), float(s.std())


def compute_inventory_recommendation(
    db: Session, product_id: int, current_stock: float | None = None
) -> Dict:
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        raise ValueError(f"Product {product_id} not found")

    sales = (
        db.query(models.Sale)
        .filter(models.Sale.product_id == product_id)
        .order_by(models.Sale.sale_date.asc())
        .all()
    )
    dates = [s.sale_date for s in sales]
    qtys = [float(s.quantity) for s in sales]

    avg_daily, std_daily = _daily_stats(dates, qtys)
    lead = int(p.lead_time_days or settings.REORDER_LEAD_DAYS)
    Z = settings.SAFETY_STOCK_Z

    # Safety Stock = Z * sigma_daily * sqrt(lead_time)
    safety_stock = Z * std_daily * math.sqrt(max(lead, 1))
    # Reorder Point = avg_daily * lead + safety_stock
    reorder_point = avg_daily * lead + safety_stock

    if current_stock is None:
        inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
        current_stock = float(inv.current_stock) if inv else 0.0

    expected_demand_horizon = avg_daily * settings.SAFETY_STOCK_DAYS
    recommended = max(0.0, expected_demand_horizon + safety_stock - current_stock)

    # Status logic
    if current_stock < safety_stock:
        status = "REORDER"
        notes = "Stock below safety stock — reorder immediately"
    elif current_stock <= reorder_point:
        status = "LOW"
        notes = "Stock at/below reorder point"
    elif current_stock > reorder_point * 3 and reorder_point > 0:
        status = "OVERSTOCK"
        notes = "Stock significantly above reorder point"
    else:
        status = "OK"
        notes = "Stock within healthy range"

    return {
        "product_id": product_id,
        "sku": p.sku,
        "name": p.name,
        "current_stock": round(current_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "safety_stock": round(safety_stock, 2),
        "recommended_order_qty": round(recommended, 2),
        "status": status,
        "notes": notes,
        "lead_time_days": lead,
        "avg_daily_demand": round(avg_daily, 2),
    }


def get_all_inventory_status(db: Session) -> List[Dict]:
    out = []
    for p in db.query(models.Product).all():
        try:
            out.append(compute_inventory_recommendation(db, p.id))
        except Exception:
            out.append({
                "product_id": p.id, "sku": p.sku, "name": p.name,
                "current_stock": 0, "reorder_point": 0, "safety_stock": 0,
                "recommended_order_qty": 0, "status": "ERROR",
                "notes": "Insufficient history", "lead_time_days": p.lead_time_days,
                "avg_daily_demand": 0,
            })
    return out
