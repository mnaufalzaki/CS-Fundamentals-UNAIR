"""Core training and cross-validation benchmark engine with checkpoint/resume support."""

import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline

from .config import (
    CHECKPOINTS_DIR,
    CONFIGURATIONS,
    DEFAULT_N_JOBS,
    N_ESTIMATORS,
    N_SPLITS_CV,
    RANDOM_STATE,
    TARGET_COL,
)
from .metrics import compute_metrics
from .models import NAN_SAFE_MODELS, get_tree_models
from .preprocessing import build_preprocessor, get_feature_columns


def build_model_pipeline(
    X_sample: pd.DataFrame,
    config_name: str,
    model_name: str,
    estimator,
) -> Pipeline:
    """Wrap fold-safe preprocessor and tree model in a single scikit-learn Pipeline."""
    allow_nan = model_name in NAN_SAFE_MODELS
    preprocessor = build_preprocessor(
        X_sample,
        config_name=config_name,
        allow_nan_passthrough=allow_nan,
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", clone(estimator)),
        ]
    )


def evaluate_single_experiment(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    config_name: str,
    model_name: str,
    estimator,
    include_customers: bool = False,
    n_splits: int = N_SPLITS_CV,
    run_cv: bool = True,
) -> Tuple[Dict, np.ndarray, Pipeline]:
    """Train on 80/20 chronological split and optionally run 5-fold TimeSeriesSplit CV."""
    t_start = time.perf_counter()
    feature_cols = get_feature_columns(
        df, config_name=config_name, include_customers=include_customers
    )

    X_train = train_df[feature_cols]
    y_train = train_df[TARGET_COL].values
    X_val = val_df[feature_cols]
    y_val = val_df[TARGET_COL].values
    y_train_mean = float(np.mean(y_train))

    # 1. Held-out 80/20 chronological evaluation
    pipe = build_model_pipeline(X_train, config_name, model_name, estimator)
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_val)
    metrics = compute_metrics(y_val, y_pred, y_train_mean)

    # 2. 5-fold TimeSeriesSplit cross-validation for stability
    cv_r2_mean = np.nan
    cv_r2_std = np.nan
    if run_cv:
        tscv = TimeSeriesSplit(n_splits=n_splits)
        X_all = df[feature_cols]
        y_all = df[TARGET_COL].values
        fold_scores = []
        for tr_idx, te_idx in tscv.split(X_all):
            X_tr_fold = X_all.iloc[tr_idx]
            y_tr_fold = y_all[tr_idx]
            X_te_fold = X_all.iloc[te_idx]
            y_te_fold = y_all[te_idx]

            fold_pipe = build_model_pipeline(X_tr_fold, config_name, model_name, estimator)
            fold_pipe.fit(X_tr_fold, y_tr_fold)
            fold_pred = fold_pipe.predict(X_te_fold)
            fold_scores.append(r2_score(y_te_fold, fold_pred))

        cv_r2_mean = float(np.mean(fold_scores))
        cv_r2_std = float(np.std(fold_scores))

    elapsed = time.perf_counter() - t_start
    row = {
        "Scenario": "With_Customers" if include_customers else "Without_Customers",
        "Config": config_name,
        "Model": model_name,
        **metrics,
        "CV_R2": cv_r2_mean,
        "CV_R2_Std": cv_r2_std,
        "Elapsed_Sec": round(elapsed, 2),
    }
    return row, y_pred, pipe


def _load_checkpoint(ckpt_csv: Path) -> Dict[Tuple[str, str], Dict]:
    """Load existing checkpoint rows keyed by (Config, Model)."""
    if not ckpt_csv.exists():
        return {}
    df_ckpt = pd.read_csv(ckpt_csv)
    existing = {}
    for record in df_ckpt.to_dict(orient="records"):
        existing[(str(record["Config"]), str(record["Model"]))] = record
    return existing


def _save_checkpoint(ckpt_csv: Path, records: Dict[Tuple[str, str], Dict]) -> None:
    """Persist checkpoint dictionary atomically to CSV."""
    ckpt_csv.parent.mkdir(parents=True, exist_ok=True)
    df_out = pd.DataFrame(list(records.values()))
    if not df_out.empty:
        df_out = df_out.sort_values(["Config", "Model"]).reset_index(drop=True)
    tmp_path = ckpt_csv.with_suffix(".tmp.csv")
    df_out.to_csv(tmp_path, index=False)
    tmp_path.replace(ckpt_csv)


def run_benchmark_suite(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    include_customers: bool = False,
    configs: Optional[List[str]] = None,
    model_names: Optional[List[str]] = None,
    n_estimators: int = N_ESTIMATORS,
    n_jobs: int = DEFAULT_N_JOBS,
    n_splits: int = N_SPLITS_CV,
    run_cv: bool = True,
    checkpoint_dir: Optional[Path] = CHECKPOINTS_DIR,
    force_rerun: bool = False,
    verbose: bool = True,
) -> Tuple[pd.DataFrame, Dict[Tuple[str, str], np.ndarray], Dict[Tuple[str, str], Pipeline]]:
    """Run tree-based models across C1-C5 with per-model checkpoint/resume support."""
    configs = configs or CONFIGURATIONS
    models = get_tree_models(
        n_estimators=n_estimators,
        random_state=RANDOM_STATE,
        n_jobs=n_jobs,
    )
    if model_names is not None:
        models = {k: v for k, v in models.items() if k in model_names}

    scenario_key = "with_customers" if include_customers else "without_customers"
    scenario_label = "With Customers" if include_customers else "Without Customers"

    ckpt_csv: Optional[Path] = None
    preds_dir: Optional[Path] = None
    ckpt_records: Dict[Tuple[str, str], Dict] = {}

    if checkpoint_dir is not None:
        ckpt_csv = Path(checkpoint_dir) / f"benchmark_{scenario_key}.csv"
        preds_dir = Path(checkpoint_dir) / "preds"
        preds_dir.mkdir(parents=True, exist_ok=True)
        if not force_rerun:
            ckpt_records = _load_checkpoint(ckpt_csv)

    predictions: Dict[Tuple[str, str], np.ndarray] = {}
    fitted_pipelines: Dict[Tuple[str, str], Pipeline] = {}

    # Also preload any previously cached predictions for downstream statistical tests
    if preds_dir is not None and not force_rerun:
        for (cfg_k, mod_k) in ckpt_records:
            pred_file = preds_dir / f"{scenario_key}_{cfg_k}_{mod_k}.npy"
            if pred_file.exists():
                arr = np.load(pred_file)
                if len(arr) == len(val_df):
                    predictions[(cfg_k, mod_k)] = arr

    for cfg in configs:
        for m_name, est in models.items():
            key = (cfg, m_name)
            pred_file = (
                preds_dir / f"{scenario_key}_{cfg}_{m_name}.npy"
                if preds_dir is not None
                else None
            )

            can_resume = (
                not force_rerun
                and key in ckpt_records
                and pred_file is not None
                and pred_file.exists()
                and len(np.load(pred_file)) == len(val_df)
            )

            if can_resume:
                row = ckpt_records[key]
                predictions[key] = np.load(pred_file)
                if verbose:
                    print(
                        f"[{scenario_label}] RESUMED {cfg} | {m_name} "
                        f"-> RMSE={row['RMSE']:.2f}, R2={row['R2']:.4f} (from checkpoint)",
                        flush=True,
                    )
                continue

            if verbose:
                print(f"[{scenario_label}] Running {cfg} | {m_name} ...", flush=True)

            row, y_pred, pipe = evaluate_single_experiment(
                df=df,
                train_df=train_df,
                val_df=val_df,
                config_name=cfg,
                model_name=m_name,
                estimator=est,
                include_customers=include_customers,
                n_splits=n_splits,
                run_cv=run_cv,
            )

            predictions[key] = y_pred
            fitted_pipelines[key] = pipe
            ckpt_records[key] = row

            if ckpt_csv is not None and pred_file is not None:
                np.save(pred_file, y_pred)
                _save_checkpoint(ckpt_csv, ckpt_records)

            if verbose:
                print(
                    f"   -> RMSE={row['RMSE']:.2f} ({row['RMSE%']:.2f}%), "
                    f"MAE={row['MAE']:.2f}, R2={row['R2']:.4f}, "
                    f"CV_R2={row['CV_R2']:.4f} (std={row['CV_R2_Std']:.4f}) "
                    f"[{row['Elapsed_Sec']:.2f}s]",
                    flush=True,
                )

    df_res = pd.DataFrame(list(ckpt_records.values()))
    if not df_res.empty:
        df_res = df_res.sort_values(["Config", "Model"]).reset_index(drop=True)
    return df_res, predictions, fitted_pipelines
