"""Statistical significance testing: Diebold-Mariano with Newey-West HAC and Holm-Bonferroni."""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from .config import DATE_COL, DM_HAC_LAG


def newey_west_variance(d: np.ndarray, lag: int = DM_HAC_LAG) -> float:
    """Compute Newey-West heteroskedasticity and autocorrelation consistent (HAC) variance."""
    d = np.asarray(d, dtype=float)
    T = len(d)
    if T <= 1:
        return 0.0

    d_centered = d - np.mean(d)
    gamma_0 = np.dot(d_centered, d_centered) / T
    var = gamma_0

    max_lag = min(lag, T - 1)
    for k in range(1, max_lag + 1):
        weight = 1.0 - (k / (max_lag + 1.0))
        gamma_k = np.dot(d_centered[k:], d_centered[:-k]) / T
        var += 2.0 * weight * gamma_k

    return max(float(var), 1e-12)


def diebold_mariano_daily(
    dates: pd.Series,
    y_true: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    loss: str = "MAE",
    lag: int = DM_HAC_LAG,
) -> Dict[str, float]:
    """Run Diebold-Mariano test on daily aggregated loss differentials (A - B).

    A negative Mean Daily Delta and negative DM Stat indicate Model A has lower
    error than Model B.
    """
    err_a = np.abs(y_true - pred_a) if loss == "MAE" else (y_true - pred_a) ** 2
    err_b = np.abs(y_true - pred_b) if loss == "MAE" else (y_true - pred_b) ** 2

    daily_df = pd.DataFrame(
        {
            "date": pd.to_datetime(dates).values,
            "loss_a": err_a,
            "loss_b": err_b,
        }
    )
    daily_agg = daily_df.groupby("date", sort=True)[["loss_a", "loss_b"]].mean()
    d = (daily_agg["loss_a"] - daily_agg["loss_b"]).values
    T = len(d)

    mean_d = float(np.mean(d))
    hac_var = newey_west_variance(d, lag=lag)
    se = np.sqrt(hac_var / T)
    dm_stat = float(mean_d / se) if se > 0 else 0.0
    p_value = float(2.0 * stats.norm.sf(abs(dm_stat)))

    return {
        "T_days": T,
        "Mean_Daily_Delta": mean_d,
        "DM_Stat": dm_stat,
        "p_Raw": p_value,
    }


def holm_bonferroni_adjust(p_values: List[float]) -> List[float]:
    """Apply Holm-Bonferroni step-down correction to a family of p-values."""
    m = len(p_values)
    if m == 0:
        return []

    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * m
    running_max = 0.0

    for rank, (orig_idx, p_val) in enumerate(indexed):
        adj = min(1.0, p_val * (m - rank))
        running_max = max(running_max, adj)
        adjusted[orig_idx] = running_max

    return adjusted


def significance_marker(p_val: float) -> str:
    """Return standard paper significance markers."""
    if p_val < 0.001:
        return "***"
    if p_val < 0.01:
        return "**"
    if p_val < 0.05:
        return "*"
    return "ns"


def run_diebold_mariano_suite(
    val_df: pd.DataFrame,
    comparisons: List[Tuple[str, np.ndarray, np.ndarray]],
    lag: int = DM_HAC_LAG,
) -> pd.DataFrame:
    """Run MAE and MSE Diebold-Mariano tests across all comparisons with Holm correction."""
    dates = val_df[DATE_COL]
    y_true = val_df["Sales"].values

    rows = []
    for label, pred_a, pred_b in comparisons:
        for loss in ("MAE", "MSE"):
            res = diebold_mariano_daily(
                dates=dates,
                y_true=y_true,
                pred_a=pred_a,
                pred_b=pred_b,
                loss=loss,
                lag=lag,
            )
            rows.append(
                {
                    "Comparison": label,
                    "Loss": loss,
                    **res,
                }
            )

    df_res = pd.DataFrame(rows)
    if not df_res.empty:
        p_holm = holm_bonferroni_adjust(df_res["p_Raw"].tolist())
        df_res["p_Holm"] = p_holm
        df_res["Sig"] = [significance_marker(p) for p in p_holm]
    return df_res
