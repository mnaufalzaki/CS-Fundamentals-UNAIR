"""One-factor-at-a-time sensitivity analysis for Rossmann without Customers under C3 (Table 12)."""

import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor

from .config import DEFAULT_N_JOBS, N_SPLITS_CV, RANDOM_STATE
from .evaluation import evaluate_single_experiment


def run_sensitivity_analysis(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    n_splits: int = N_SPLITS_CV,
    n_jobs: int = DEFAULT_N_JOBS,
    run_cv: bool = True,
    verbose: bool = True,
) -> pd.DataFrame:
    """Evaluate ensemble size (50, 100, 200) and reduced complexity (max_depth=15)
    for RandomForest and ExtraTrees under C3 without Customers."""
    specs = [
        ("RandomForest", "Reference (n_estimators=100)", RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("RandomForest", "n_estimators = 50", RandomForestRegressor(n_estimators=50, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("RandomForest", "n_estimators = 200", RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("RandomForest", "max_depth = 15 (reduced complexity)", RandomForestRegressor(n_estimators=100, max_depth=15, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("ExtraTrees", "Reference (n_estimators=100)", ExtraTreesRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("ExtraTrees", "n_estimators = 50", ExtraTreesRegressor(n_estimators=50, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("ExtraTrees", "n_estimators = 200", ExtraTreesRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=n_jobs)),
        ("ExtraTrees", "max_depth = 15 (reduced complexity)", ExtraTreesRegressor(n_estimators=100, max_depth=15, random_state=RANDOM_STATE, n_jobs=n_jobs)),
    ]

    rows = []
    for model_name, setting_label, estimator in specs:
        if verbose:
            print(f"[Sensitivity] {model_name} | {setting_label} ...", flush=True)
        row, _, _ = evaluate_single_experiment(
            df=df,
            train_df=train_df,
            val_df=val_df,
            config_name="C3",
            model_name=model_name,
            estimator=estimator,
            include_customers=False,
            n_splits=n_splits,
            run_cv=run_cv,
        )
        rows.append(
            {
                "Model": model_name,
                "Hyperparameter_Setting": setting_label,
                "RMSE": row["RMSE"],
                "RMSE%": row["RMSE%"],
                "MAE": row["MAE"],
                "R2": row["R2"],
                "CV_R2": row["CV_R2"],
                "CV_R2_Std": row["CV_R2_Std"],
                "Elapsed_Sec": row["Elapsed_Sec"],
            }
        )

    return pd.DataFrame(rows)
