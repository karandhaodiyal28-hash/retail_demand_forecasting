"""Generate sample_sales.csv for direct CSV import testing.

Run:  python -m backend.generate_sample_csv
"""
from __future__ import annotations
import csv
import random
from datetime import date, timedelta
from pathlib import Path

from .config import settings
from .seed_data import SAMPLE_PRODUCTS, _gen_sales_series


def generate():
    path = settings.SAMPLE_DATA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    start = date.today() - timedelta(days=400)
    rows = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sku", "sale_date", "quantity", "revenue"])
        for idx, (sku, _name, _cat, _cost, price, _lt) in enumerate(SAMPLE_PRODUCTS):
            base = random.Random(idx).uniform(15, 80)
            weekly_peak = random.Random(idx + 100).uniform(1.3, 1.8)
            monthly_peak = random.Random(idx + 200).uniform(1.5, 2.2)
            growth = random.Random(idx + 300).uniform(-0.15, 0.4)
            noise = random.Random(idx + 400).uniform(0.10, 0.25)
            series = _gen_sales_series(start, 400, base, weekly_peak,
                                       monthly_peak, growth, noise, seed=idx + 1000)
            for d, q in series:
                w.writerow([sku, d.isoformat(), q, round(q * price, 2)])
                rows += 1
    print(f"Wrote {rows} rows to {path}")


if __name__ == "__main__":
    generate()
