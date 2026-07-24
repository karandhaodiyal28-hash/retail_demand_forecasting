"""Sample data seeding.

* 20 retail products across 5 categories
* ~400 days of daily sales per product
* Initial admin user (admin / Admin@123) — change immediately after first login
"""
from __future__ import annotations
import random
from datetime import date, timedelta
from typing import List, Tuple

from sqlalchemy.orm import Session

from .database import SessionLocal, init_db
from . import models
from .auth import hash_password


SAMPLE_PRODUCTS: List[Tuple[str, str, str, float, float, int]] = [
    # (sku,                       name,                                category,    cost, price, lead)
    ("FLR-001",  "Premium Wheat Flour 5kg",                 "Grocery",     180, 250, 5),
    ("FLR-002",  "Multigrain Atta 10kg",                    "Grocery",     380, 520, 5),
    ("RIC-001",  "Basmati Rice 5kg",                        "Grocery",     420, 580, 4),
    ("RIC-002",  "Sona Masoori Rice 10kg",                  "Grocery",     580, 780, 4),
    ("OIL-001",  "Cold-Pressed Mustard Oil 1L",             "Grocery",     165, 240, 3),
    ("OIL-002",  "Refined Sunflower Oil 5L",                "Grocery",     540, 720, 3),
    ("SNK-001",  "Masala Noodles 200g x 12",                "Snacks",       90, 144, 2),
    ("SNK-002",  "Potato Chips Classic 50g x 24",           "Snacks",       72, 120, 2),
    ("SNK-003",  "Premium Mixed Cookies 600g",              "Snacks",      150, 250, 3),
    ("BVR-001",  "Cola Soft Drink 2L",                      "Beverages",    60,  90, 2),
    ("BVR-002",  "Mango Juice 1L",                          "Beverages",    85, 130, 2),
    ("BVR-003",  "Green Tea Bags 100ct",                    "Beverages",   180, 280, 4),
    ("DRY-001",  "Toor Dal 1kg",                            "Grocery",     130, 185, 4),
    ("DRY-002",  "Moong Dal 1kg",                           "Grocery",     140, 200, 4),
    ("DRY-003",  "Kabuli Chana 500g",                       "Grocery",      75, 115, 4),
    ("HOM-001",  "Liquid Detergent 1L",                     "Household",   110, 175, 3),
    ("HOM-002",  "Floor Cleaner 1L",                        "Household",    85, 135, 3),
    ("PER-001",  "Anti-Dandruff Shampoo 650ml",              "Personal Care", 180, 280, 3),
    ("PER-002",  "Toothpaste 200g x 2",                     "Personal Care", 95, 150, 3),
    ("PER-003",  "Bath Soap 125g x 4",                      "Personal Care", 70, 110, 3),
]


def _gen_sales_series(
    start: date,
    days: int,
    base: float,
    weekly_peak: float,
    monthly_peak: float,
    growth: float,
    noise: float,
    seed: int,
):
    """Generate a realistic daily sales series with weekly/monthly seasonality + trend + noise."""
    rng = random.Random(seed)
    out: List[Tuple[date, float]] = []
    for i in range(days):
        d = start + timedelta(days=i)
        weekly = weekly_peak if d.weekday() in (5, 6) else 1.0
        monthly = monthly_peak if d.day in (1, 2, 3, 28, 29, 30, 31) else 1.0
        growth_factor = 1.0 + growth * (i / max(days, 1))
        noise_factor = 1.0 + rng.uniform(-noise, noise)
        qty = max(0.0, base * weekly * monthly * growth_factor * noise_factor)
        out.append((d, round(qty, 2)))
    return out


def seed(force: bool = False) -> None:
    """Initialise the DB and insert sample data.  Idempotent unless force=True."""
    init_db()
    db: Session = SessionLocal()
    try:
        # Admin user (idempotent)
        if not db.query(models.User).filter(models.User.username == "admin").first():
            db.add(models.User(
                username="admin",
                email="[email protected]",
                full_name="Default Admin",
                hashed_password=hash_password("Admin@123"),
                role="admin",
                is_active=1,
            ))
            db.commit()
            print("  created default admin user  (username=admin  password=Admin@123)")

        if force:
            db.query(models.Sale).delete()
            db.query(models.Forecast).delete()
            db.query(models.Inventory).delete()
            db.query(models.Product).delete()
            db.commit()

        if db.query(models.Product).count() > 0:
            print("  sample products already present — skipping")
            return

        products = []
        for sku, name, cat, cost, price, lead in SAMPLE_PRODUCTS:
            p = models.Product(
                sku=sku, name=name, category=cat,
                unit_cost=cost, unit_price=price, lead_time_days=lead,
            )
            db.add(p)
            products.append(p)
        db.commit()

        start = date.today() - timedelta(days=400)
        for idx, p in enumerate(products):
            base = random.Random(idx).uniform(15, 80)
            weekly_peak = random.Random(idx + 100).uniform(1.2, 1.6)
            monthly_peak = random.Random(idx + 200).uniform(1.3, 1.7)
            growth = random.Random(idx + 300).uniform(-0.10, 0.30)
            noise = random.Random(idx + 400).uniform(0.08, 0.20)
            series = _gen_sales_series(
                start, 400, base, weekly_peak, monthly_peak, growth, noise, seed=idx + 1000,
            )
            for d, q in series:
                db.add(models.Sale(
                    product_id=p.id, sale_date=d, quantity=q, revenue=round(q * p.unit_price, 2),
                ))
        db.commit()
        print(f"  inserted {len(products)} products + {len(products) * 400} sales rows")
    finally:
        db.close()


if __name__ == "__main__":
    seed(force="--force" in __import__("sys").argv)
