"""Classical forecasting baselines (Section 3.7): Ridge, Seasonal-Naive, and per-store ETS."""

import warnings
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline

from .config import DATE_COL, N_SPLITS_CV, STORE_COL, TARGET_COL
from .metrics import compute_metrics
from .preprocessing import build_preprocessor, get_feature_columns

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


def predict_seasonal_naive(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    max_weeks_backoff: int = 8,
) -> np.ndarray:
    """Seasonal-Naive (lag-7) baseline with recent-week backoff and store-mean fallback.

    Predicts each day's sales as the actual sales from the same store on the same
    weekday in a prior week, backing off over recent weeks if that day was closed
    or missing, and falling back to the training-period store mean.
    """
    global_mean = float(train_df[TARGET_COL].mean())
    store_means = train_df.groupby(STORE_COL)[TARGET_COL].mean().to_dict()

    # Build lookup of (Store, Date) -> Sales from history (train + observed val sequentially)
    # Using strictly historical training observations for multi-step held-out forecast:
    lookup: Dict[Tuple[int, pd.Timestamp], float] = {
        (int(s), d): float(y)
        for s, d, y in zip(
            train_df[STORE_COL].values,
            train_df[DATE_COL].values,
            train_df[TARGET_COL].values,
        )
    }

    # Also build per-(Store, DayOfWeek) last known observation from training data
    last_weekday_val: Dict[Tuple[int, int], float] = {}
    train_sorted = train_df.sort_values(DATE_COL)
    for (s, dow), grp in train_sorted.groupby([STORE_COL, "DayOfWeek"]):
        last_weekday_val[(int(s), int(dow))] = float(grp[TARGET_COL].iloc[-1])

    preds = np.empty(len(val_df), dtype=float)
    stores = val_df[STORE_COL].values
    dates = val_df[DATE_COL].values
    dows = val_df["DayOfWeek"].values

    for i in range(len(val_df)):
        store = int(stores[i])
        date = pd.Timestamp(dates[i])
        found = None

        for w in range(1, max_weeks_backoff + 1):
            prior_date = date - pd.Timedelta(days=7 * w)
            val = lookup.get((store, prior_date))
            if val is not None:
                found = val
                break

        if found is None:
            found = last_weekday_val.get((store, int(dows[i])))
        if found is None:
            found = store_means.get(store, global_mean)

        preds[i] = found

    return preds


def predict_ets_per_store(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
) -> np.ndarray:
    """Per-store Holt-Winters ETS (additive damped trend + additive weekly seasonality)."""
    if not HAS_STATSMODELS:
        raise ImportError(
            "statsmodels is required for the per-store ETS baseline. "
            "Install it with: pip install statsmodels"
        )

    global_mean = float(train_df[TARGET_COL].mean())
    preds = np.full(len(val_df), global_mean, dtype=float)

    train_groups = {
        int(s): grp.sort_values(DATE_COL)
        for s, grp in train_df.groupby(STORE_COL)
    }

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for store, val_grp in val_df.groupby(STORE_COL):
            store_id = int(store)
            val_indices = val_grp.index.values
            train_grp = train_groups.get(store_id)

            if train_grp is None or len(train_grp) < 14:
                fallback = (
                    float(train_grp[TARGET_COL].mean())
                    if train_grp is not None and len(train_grp) > 0
                    else global_mean
                )
                preds[val_indices] = fallback
                continue

            series = train_grp[TARGET_COL].astype(float).values
            horizon = len(val_indices)

            try:
                model = ExponentialSmoothing(
                    series,
                    trend="add",
                    damped_trend=True,
                    seasonal="add",
                    seasonal_periods=7,
                )
                fit = model.fit(optimized=True, use_brute=False)
                forecast = np.asarray(fit.forecast(horizon), dtype=float)
                if np.any(~np.isfinite(forecast)):
                    raise ValueError("Non-finite ETS forecast")
                preds[val_indices] = np.clip(forecast, 0.0, None)
            except Exception:
                preds[val_indices] = float(np.mean(series))

    return preds


def evaluate_classical_baselines(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    n_splits: int = N_SPLITS_CV,
    run_ets: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """Evaluate Ridge Regression, Seasonal-Naive, and per-store ETS under C3 without Customers."""
    y_train_mean = float(train_df[TARGET_COL].mean())
    y_val = val_df[TARGET_COL].values
    tscv = TimeSeriesSplit(n_splits=n_splits)

    results = []
    val_predictions: Dict[str, np.ndarray] = {}

    # 1. Ridge Regression (C3 preprocessing pipeline, alpha=1.0)
    feature_cols = get_feature_columns(df, config_name="C3", include_customers=False)
    X_train = train_df[feature_cols]
    y_train = train_df[TARGET_COL].values
    X_val = val_df[feature_cols]

    ridge_pipe = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(X_train, config_name="C3")),
            ("model", Ridge(alpha=1.0)),
        ]
    )
    ridge_pipe.fit(X_train, y_train)
    ridge_pred = ridge_pipe.predict(X_val)
    val_predictions["Ridge Regression"] = ridge_pred
    ridge_metrics = compute_metrics(y_val, ridge_pred, y_train_mean)

    ridge_cv_scores = []
    X_all = df[feature_cols]
    y_all = df[TARGET_COL].values
    for tr_idx, te_idx in tscv.split(X_all):
        pipe_cv = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor(X_all.iloc[tr_idx], config_name="C3")),
                ("model", Ridge(alpha=1.0)),
            ]
        )
        pipe_cv.fit(X_all.iloc[tr_idx], y_all[tr_idx])
        pred_cv = pipe_cv.predict(X_all.iloc[te_idx])
        ridge_cv_scores.append(r2_score(y_all[te_idx], pred_cv))

    results.append(
        {
            "Model": "Ridge Regression",
            **ridge_metrics,
            "CV_R2": float(np.mean(ridge_cv_scores)),
            "CV_R2_Std": float(np.std(ridge_cv_scores)),
        }
    )

    # 2. Seasonal-Naive (lag-7)
    sn_pred = predict_seasonal_naive(train_df, val_df)
    val_predictions["Seasonal-Naive"] = sn_pred
    sn_metrics = compute_metrics(y_val, sn_pred, y_train_mean)

    sn_cv_scores = []
    for tr_idx, te_idx in tscv.split(df):
        tr_fold = df.iloc[tr_idx]
        te_fold = df.iloc[te_idx]
        pred_cv = predict_seasonal_naive(tr_fold, te_fold)
        sn_cv_scores.append(r2_score(te_fold[TARGET_COL].values, pred_cv))

    results.append(
        {
            "Model": "Seasonal-Naive",
            **sn_metrics,
            "CV_R2": float(np.mean(sn_cv_scores)),
            "CV_R2_Std": float(np.std(sn_cv_scores)),
        }
    )

    # 3. ETS (per-store Holt-Winters)
    if run_ets and HAS_STATSMODELS:
        ets_pred = predict_ets_per_store(train_df, val_df)
        val_predictions["ETS"] = ets_pred
        ets_metrics = compute_metrics(y_val, ets_pred, y_train_mean)

        ets_cv_scores = []
        for tr_idx, te_idx in tscv.split(df):
            tr_fold = df.iloc[tr_idx].reset_index(drop=True)
            te_fold = df.iloc[te_idx].reset_index(drop=True)
            pred_cv = predict_ets_per_store(tr_fold, te_fold)
            ets_cv_scores.append(r2_score(te_fold[TARGET_COL].values, pred_cv))

        results.append(
            {
                "Model": "ETS",
                **ets_metrics,
                "CV_R2": float(np.mean(ets_cv_scores)),
                "CV_R2_Std": float(np.std(ets_cv_scores)),
            }
        )
    elif run_ets and not HAS_STATSMODELS:
        print("[WARN] statsmodels not installed; skipping ETS baseline.")

    return pd.DataFrame(results), val_predictions
