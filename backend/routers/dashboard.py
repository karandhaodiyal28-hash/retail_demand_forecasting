"""Dashboard endpoints - aggregated stats (auth required)."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models
from ..auth import get_current_user


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    total_products = db.query(models.Product).count()
    total_sales = db.query(models.Sale).count()
    total_revenue = db.query(func.sum(models.Sale.revenue)).scalar() or 0.0

    latest_forecasts = (
        db.query(models.Forecast)
        .order_by(models.Forecast.created_at.desc())
        .limit(500)
        .all()
    )
    avg_forecast = (
        sum(f.predicted_quantity for f in latest_forecasts) / len(latest_forecasts)
        if latest_forecasts else 0.0
    )

    low_stock_count = db.query(models.Inventory).filter(
        models.Inventory.current_stock <= models.Inventory.reorder_point
    ).count()

    cutoff = date.today() - timedelta(days=90)
    top_rows = (
        db.query(models.Product, func.sum(models.Sale.revenue).label("rev"))
        .join(models.Sale, models.Sale.product_id == models.Product.id)
        .filter(models.Sale.sale_date >= cutoff)
        .group_by(models.Product.id)
        .order_by(func.sum(models.Sale.revenue).desc())
        .limit(5)
        .all()
    )
    top_products = [
        {"sku": p.sku, "name": p.name, "revenue": round(float(rev or 0), 2)}
        for p, rev in top_rows
    ]

    recent = (
        db.query(models.Forecast, models.Product)
        .join(models.Product, models.Product.id == models.Forecast.product_id)
        .order_by(models.Forecast.created_at.desc())
        .limit(10)
        .all()
    )
    recent_forecasts = [
        {
            "product_sku": p.sku,
            "product_name": p.name,
            "model": f.model_name,
            "date": str(f.forecast_date),
            "predicted": f.predicted_quantity,
        }
        for f, p in recent
    ]

    return {
        "total_products": total_products,
        "total_sales_records": total_sales,
        "total_revenue": round(float(total_revenue), 2),
        "avg_forecast_30d": round(float(avg_forecast), 2),
        "low_stock_count": low_stock_count,
        "top_products": top_products,
        "recent_forecasts": recent_forecasts,
    }


@router.get("/revenue-trend")
def revenue_trend(
    days: int = 30,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    days = max(1, min(days, 365))
    cutoff = date.today() - timedelta(days=days)
    rows = (
        db.query(models.Sale.sale_date, func.sum(models.Sale.revenue).label("rev"))
        .filter(models.Sale.sale_date >= cutoff)
        .group_by(models.Sale.sale_date)
        .order_by(models.Sale.sale_date.asc())
        .all()
    )
    return [
        {"date": str(d), "revenue": round(float(r or 0), 2)}
        for d, r in rows
    ]


@router.get("/category-breakdown")
def category_breakdown(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    rows = (
        db.query(models.Product.category, func.sum(models.Sale.revenue).label("rev"))
        .join(models.Sale, models.Sale.product_id == models.Product.id)
        .group_by(models.Product.category)
        .order_by(func.sum(models.Sale.revenue).desc())
        .all()
    )
    return [
        {"category": c or "Uncategorized", "revenue": round(float(r or 0), 2)}
        for c, r in rows
    ]


@router.get("/demand-trend")
def demand_trend(
    days: int = 30,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Store-wide historical sales units + aggregated predicted demand.

    * historical: total units sold per day over the trailing ``days`` window.
    * predicted:  total predicted units per future day, averaged across models
                  per product (so a product forecast by 3 models is not counted
                  three times) and summed across all products.
    """
    days = max(7, min(days, 180))
    today = date.today()
    cutoff = today - timedelta(days=days)

    hist_rows = (
        db.query(models.Sale.sale_date, func.sum(models.Sale.quantity).label("units"))
        .filter(models.Sale.sale_date >= cutoff, models.Sale.sale_date <= today)
        .group_by(models.Sale.sale_date)
        .order_by(models.Sale.sale_date.asc())
        .all()
    )
    historical = [
        {"date": str(d), "units": round(float(u or 0), 2)} for d, u in hist_rows
    ]

    # Average predicted qty across models for each (product, date), then sum per date.
    per_product = (
        db.query(
            models.Forecast.product_id,
            models.Forecast.forecast_date,
            func.avg(models.Forecast.predicted_quantity).label("q"),
        )
        .filter(models.Forecast.forecast_date > today)
        .group_by(models.Forecast.product_id, models.Forecast.forecast_date)
        .subquery()
    )
    pred_rows = (
        db.query(per_product.c.forecast_date, func.sum(per_product.c.q).label("units"))
        .group_by(per_product.c.forecast_date)
        .order_by(per_product.c.forecast_date.asc())
        .limit(days)
        .all()
    )
    predicted = [
        {"date": str(d), "units": round(float(u or 0), 2)} for d, u in pred_rows
    ]

    return {"historical": historical, "predicted": predicted}

