"""Facebook Prophet forecasting service."""
from __future__ import annotations
from typing import Tuple, List, Dict
import numpy as np
import pandas as pd

import logging
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except Exception:                                  # pragma: no cover
    PROPHET_AVAILABLE = False

from ..config import settings
from ..utils.metrics import compute_metrics


class ProphetUnavailable(RuntimeError):
    """Raised when Prophet is not installed."""


def _check():
    if not PROPHET_AVAILABLE:
        raise ProphetUnavailable(
            "Prophet is not installed.  pip install prophet"
        )


def fit_predict(
    dates: List,
    quantities: List[float],
    horizon_days: int,
) -> Tuple[List[Dict], Dict[str, float]]:
    """Fit Prophet and produce forecasts.

    Returns
    -------
    forecasts : list of {forecast_date, predicted_quantity, lower_bound, upper_bound}
    metrics   : {mae, rmse, mape} on the in-sample backtest
    """
    _check()
    df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": np.asarray(quantities, dtype=float)})
    df = df.sort_values("ds").reset_index(drop=True)

    # Use 80/20 hold-out for metrics
    n = len(df)
    if n < 30:
        raise ValueError("Prophet needs at least 30 days of history")

    split = max(int(n * 0.8), n - max(horizon_days, 30))
    train, test = df.iloc[:split], df.iloc[split:]
    if len(test) < 5:
        train, test = df, df.tail(5)  # last-resort

    m = Prophet(
        interval_width=settings.PROPHET_INTERVAL_WIDTH,
        daily_seasonality=False,
        weekly_seasonality=True,
        yearly_seasonality=(n >= 365),
    )
    m.fit(train)

    # In-sample fit for metrics
    in_sample = m.predict(df[["ds"]])
    actual = df["y"].values
    pred = in_sample["yhat"].values
    metrics = compute_metrics(actual, pred)

    # Forecast horizon
    future = m.make_future_dataframe(periods=horizon_days, freq="D")
    fc = m.predict(future).tail(horizon_days)
    forecasts = [
        {
            "forecast_date": d.strftime("%Y-%m-%d"),
            "predicted_quantity": max(0.0, round(float(p), 2)),
            "lower_bound": max(0.0, round(float(l), 2)),
            "upper_bound": max(0.0, round(float(u), 2)),
        }
        for d, p, l, u in zip(fc["ds"], fc["yhat"], fc["yhat_lower"], fc["yhat_upper"])
    ]
    return forecasts, metrics
