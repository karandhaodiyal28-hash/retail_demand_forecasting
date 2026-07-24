"""XGBoost forecasting service with engineered lag/rolling features."""
from __future__ import annotations
from typing import Tuple, List, Dict
import numpy as np
import pandas as pd

try:
    from xgboost import XGBRegressor
    XGB_AVAILABLE = True
except Exception:                                  # pragma: no cover
    XGB_AVAILABLE = False

from ..config import settings
from ..utils.metrics import compute_metrics


class XGBUnavailable(RuntimeError):
    pass


def _check():
    if not XGB_AVAILABLE:
        raise XGBUnavailable("XGBoost is not installed.  pip install xgboost")


def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calendar + lag + rolling features."""
    out = df.copy()
    out["dow"] = out["ds"].dt.dayofweek
    out["dom"] = out["ds"].dt.day
    out["month"] = out["ds"].dt.month
    out["woy"] = out["ds"].dt.isocalendar().week.astype(int)
    out["is_weekend"] = (out["dow"] >= 5).astype(int)
    out["trend"] = np.arange(len(out))

    for lag in (1, 7, 14, 28):
        out[f"lag_{lag}"] = out["y"].shift(lag)
    for win in (7, 14, 28):
        out[f"roll_mean_{win}"] = out["y"].shift(1).rolling(win).mean()
        out[f"roll_std_{win}"] = out["y"].shift(1).rolling(win).std()

    out = out.dropna().reset_index(drop=True)
    return out


FEATURE_COLS = [
    "dow", "dom", "month", "woy", "is_weekend", "trend",
    "lag_1", "lag_7", "lag_14", "lag_28",
    "roll_mean_7", "roll_std_7", "roll_mean_14", "roll_std_14",
    "roll_mean_28", "roll_std_28",
]


def fit_predict(
    dates: List,
    quantities: List[float],
    horizon_days: int,
) -> Tuple[List[Dict], Dict[str, float]]:
    _check()
    df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": np.asarray(quantities, dtype=float)})
    df = df.sort_values("ds").reset_index(drop=True)
    if len(df) < 35:
        raise ValueError("XGBoost needs at least 35 days of history")

    feat = _build_features(df)
    n = len(feat)

    # Hold out the last `horizon_days` rows for backtest
    test_n = min(max(horizon_days, 7), n // 4)
    train = feat.iloc[:-test_n]
    test = feat.iloc[-test_n:]

    X_tr, y_tr = train[FEATURE_COLS], train["y"]
    X_te, y_te = test[FEATURE_COLS], test["y"]

    model = XGBRegressor(
        n_estimators=settings.XGB_N_ESTIMATORS,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=2,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    y_pred_test = model.predict(X_te)
    metrics = compute_metrics(y_te.values, y_pred_test)

    # Recursive forecast: build features iteratively
    history = df.copy()
    forecasts: List[Dict] = []
    last_date = history["ds"].iloc[-1]
    for i in range(1, horizon_days + 1):
        next_date = last_date + pd.Timedelta(days=i)
        new_row = pd.DataFrame({"ds": [next_date], "y": [np.nan]})
        tmp = pd.concat([history, new_row], ignore_index=True)
        feat2 = _build_features(tmp)
        x_next = feat2[FEATURE_COLS].iloc[[-1]]
        y_hat = float(model.predict(x_next)[0])
        # write back so lag/rolling features use this prediction
        history = pd.concat([history, pd.DataFrame({"ds": [next_date], "y": [y_hat]})], ignore_index=True)
        # XGBoost has no native intervals; widen by ±15% of recent residual std
        std_dev = float(np.std(y_pred_test - y_te.values)) if len(y_te) > 1 else y_hat * 0.1
        forecasts.append({
            "forecast_date": next_date.strftime("%Y-%m-%d"),
            "predicted_quantity": max(0.0, round(y_hat, 2)),
            "lower_bound": max(0.0, round(y_hat - 1.96 * std_dev, 2)),
            "upper_bound": max(0.0, round(y_hat + 1.96 * std_dev, 2)),
        })
    return forecasts, metrics
