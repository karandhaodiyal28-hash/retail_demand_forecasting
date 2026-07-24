"""Seasonal analysis utilities."""
from __future__ import annotations
from typing import List, Dict
import numpy as np
import pandas as pd


def analyze_seasonality(dates: List, quantities: List[float]) -> Dict:
    """Compute weekly/monthly seasonality, trend, peak day, peak month."""
    df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": np.asarray(quantities, dtype=float)})
    df = df.sort_values("ds").reset_index(drop=True)
    if len(df) == 0:
        return {}

    df["dow"] = df["ds"].dt.day_name()
    df["month"] = df["ds"].dt.month_name()

    dow_avg = df.groupby("dow")["y"].mean().to_dict()
    month_avg = df.groupby("month")["y"].mean().to_dict()

    # Order dow correctly
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_series = {d: round(float(dow_avg.get(d, 0)), 2) for d in dow_order}

    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    month_series = {m: round(float(month_avg.get(m, 0)), 2) for m in month_order}

    # Linear trend (slope per day)
    if len(df) >= 2:
        x = np.arange(len(df))
        slope = float(np.polyfit(x, df["y"].values, 1)[0])
    else:
        slope = 0.0

    peak_dow = max(dow_series, key=dow_series.get) if dow_series else None
    peak_month = max(month_series, key=month_series.get) if month_series else None

    return {
        "weekly_pattern": dow_series,
        "monthly_pattern": month_series,
        "trend_slope_per_day": round(slope, 4),
        "trend_direction": "up" if slope > 0 else "down" if slope < 0 else "flat",
        "peak_weekday": peak_dow,
        "peak_month": peak_month,
        "avg_daily": round(float(df["y"].mean()), 2),
        "max_daily": round(float(df["y"].max()), 2),
        "min_daily": round(float(df["y"].min()), 2),
        "std_daily": round(float(df["y"].std()), 2),
    }
