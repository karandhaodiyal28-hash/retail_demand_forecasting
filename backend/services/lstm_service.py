"""LSTM forecasting service backed by TensorFlow / Keras."""
from __future__ import annotations
from typing import Tuple, List, Dict
import os
import numpy as np
import pandas as pd

# Suppress TF chatter before importing
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
    from tensorflow.keras.callbacks import EarlyStopping
    TF_AVAILABLE = True
except Exception:                                  # pragma: no cover
    TF_AVAILABLE = False

from ..config import settings
from ..utils.metrics import compute_metrics


class LSTMUnavailable(RuntimeError):
    pass


def _check():
    if not TF_AVAILABLE:
        raise LSTMUnavailable("TensorFlow is not installed.  pip install tensorflow")


def _make_model(n_features: int) -> "Sequential":
    m = Sequential([
        Input(shape=(settings.LSTM_SEQUENCE_LENGTH, n_features)),
        LSTM(50, activation="relu"),
        Dropout(0.2),
        Dense(25, activation="relu"),
        Dense(1),
    ])
    m.compile(optimizer="adam", loss="mse")
    return m


def fit_predict(
    dates: List,
    quantities: List[float],
    horizon_days: int,
) -> Tuple[List[Dict], Dict[str, float]]:
    _check()
    df = pd.DataFrame({"ds": pd.to_datetime(dates), "y": np.asarray(quantities, dtype=float)})
    df = df.sort_values("ds").reset_index(drop=True)
    if len(df) < settings.LSTM_SEQUENCE_LENGTH + 30:
        raise ValueError(
            f"LSTM needs at least {settings.LSTM_SEQUENCE_LENGTH + 30} days of history"
        )

    series = df["y"].values.astype(float)
    mean = series.mean()
    std = series.std() + 1e-6
    normed = (series - mean) / std

    seq_len = settings.LSTM_SEQUENCE_LENGTH
    X, y = [], []
    for i in range(len(normed) - seq_len):
        X.append(normed[i:i + seq_len])
        y.append(normed[i + seq_len])
    X = np.asarray(X).reshape(-1, seq_len, 1)
    y = np.asarray(y)

    # Hold out 15% for validation
    split = int(len(X) * 0.85)
    X_tr, X_va = X[:split], X[split:]
    y_tr, y_va = y[:split], y[split:]

    model = _make_model(n_features=1)
    model.fit(
        X_tr, y_tr,
        validation_data=(X_va, y_va) if len(X_va) > 0 else None,
        epochs=settings.LSTM_EPOCHS,
        batch_size=16,
        verbose=0,
        callbacks=[EarlyStopping(patience=3, restore_best_weights=True)] if len(X_va) > 0 else None,
    )

    # In-sample metrics
    in_pred = model.predict(X, verbose=0).flatten()
    actual = y * std + mean
    pred = in_pred * std + mean
    metrics = compute_metrics(actual, pred)

    # Recursive forecast
    window = list(normed[-seq_len:])
    forecasts: List[Dict] = []
    last_date = df["ds"].iloc[-1]
    residuals = actual - pred
    std_dev = float(np.std(residuals)) * std if len(residuals) > 1 else mean * 0.1

    for i in range(1, horizon_days + 1):
        x_in = np.asarray(window[-seq_len:]).reshape(1, seq_len, 1)
        y_hat_norm = float(model.predict(x_in, verbose=0)[0, 0])
        y_hat = y_hat_norm * std + mean
        window.append(y_hat_norm)
        next_date = last_date + pd.Timedelta(days=i)
        forecasts.append({
            "forecast_date": next_date.strftime("%Y-%m-%d"),
            "predicted_quantity": max(0.0, round(y_hat, 2)),
            "lower_bound": max(0.0, round(y_hat - 1.96 * std_dev, 2)),
            "upper_bound": max(0.0, round(y_hat + 1.96 * std_dev, 2)),
        })
    return forecasts, metrics
