"""Utilities: metrics, seasonal analysis, data loading."""
from __future__ import annotations
import numpy as np
from typing import Iterable


def compute_metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict:
    """Compute MAE, RMSE, MAPE."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    n = len(actual)
    if n == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

    err = predicted - actual
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err ** 2)))

    # MAPE with epsilon to avoid divide-by-zero
    denom = np.where(np.abs(actual) < 1e-6, 1.0, np.abs(actual))
    mape = float(np.mean(np.abs(err) / denom) * 100.0)
    if not np.isfinite(mape):
        mape = 0.0

    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 2)}
