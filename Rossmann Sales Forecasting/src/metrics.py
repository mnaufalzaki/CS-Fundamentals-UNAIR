"""Evaluation metrics matching Section 3.8 of Albassam et al. (2026)."""

from typing import Dict

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_train_mean: float,
) -> Dict[str, float]:
    """Compute MAE, RMSE, RMSE% (normalized by y_bar_train), and R2."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    rmse_pct = float((rmse / y_train_mean) * 100.0) if y_train_mean != 0 else np.nan
    r2 = float(r2_score(y_true, y_pred))
    return {
        "RMSE": rmse,
        "RMSE%": rmse_pct,
        "MAE": mae,
        "R2": r2,
    }
