"""End-to-end Rossmann experimental pipeline reproducing Albassam et al. (2026).

Usage:
    # Full experiment with automatic checkpoint/resume
    python3 run_experiments.py

    # Staged run: fast models first, then heavier models (resumes automatically)
    python3 run_experiments.py --models DecisionTree HistGradientBoosting XGBoost --skip-baselines --skip-stats --skip-sensitivity
    python3 run_experiments.py --models RandomForest ExtraTrees

    # Quick smoke test on 25 stores
    python3 run_experiments.py --sample-stores 25 --n-estimators 20 --force-rerun
"""

import argparse
from pathlib import Path

import pandas as pd

from src.baselines import evaluate_classical_baselines
from src.config import (
    CHECKPOINTS_DIR,
    CONFIGURATIONS,
    DATA_DIR,
    DEFAULT_N_JOBS,
    FIGURES_DIR,
    N_ESTIMATORS,
    N_SPLITS_CV,
    RANDOM_STATE,
    TABLES_DIR,
    TARGET_COL,
    TEST_RATIO,
)
from src.data_loader import chronological_train_val_split, load_rossmann_data
from src.evaluation import build_model_pipeline, run_benchmark_suite
from src.interpretability import (
    plot_actual_vs_predicted,
    plot_feature_importances,
    run_shap_analysis,
)
from src.models import get_tree_models
from src.preprocessing import get_feature_columns
from src.sensitivity import run_sensitivity_analysis
from src.statistics import run_diebold_mariano_suite


def build_customer_ablation_table(
    df_wo: pd.DataFrame,
    df_w: pd.DataFrame,
) -> pd.DataFrame:
    """Build Table 6: Impact of Customers feature under C3."""
    if df_wo.empty or df_w.empty:
        return pd.DataFrame()
    wo_c3 = df_wo[df_wo["Config"] == "C3"][["Model", "R2", "RMSE%"]].rename(
        columns={"R2": "R2_wo", "RMSE%": "RMSE%_wo"}
    )
    w_c3 = df_w[df_w["Config"] == "C3"][["Model", "R2", "RMSE%"]].rename(
        columns={"R2": "R2_w", "RMSE%": "RMSE%_w"}
    )
    merged = wo_c3.merge(w_c3, on="Model")
    merged["Delta_R2"] = merged["R2_w"] - merged["R2_wo"]
    merged["Delta_RMSE%"] = merged["RMSE%_w"] - merged["RMSE%_wo"]
    return merged[["Model", "R2_wo", "R2_w", "Delta_R2", "RMSE%_wo", "RMSE%_w", "Delta_RMSE%"]]


def build_seasonality_ablation_table(
    df_wo: pd.DataFrame,
    df_w: pd.DataFrame,
) -> pd.DataFrame:
    """Build Table 7: Impact of removing seasonality/promotional features (C3 vs C4)."""
    if df_wo.empty or df_w.empty:
        return pd.DataFrame()

    def _diff(df_sc: pd.DataFrame, suffix: str) -> pd.DataFrame:
        c3 = df_sc[df_sc["Config"] == "C3"][["Model", "R2", "RMSE%"]].rename(
            columns={"R2": f"R2_C3_{suffix}", "RMSE%": f"RMSE%_C3_{suffix}"}
        )
        c4 = df_sc[df_sc["Config"] == "C4"][["Model", "R2", "RMSE%"]].rename(
            columns={"R2": f"R2_C4_{suffix}", "RMSE%": f"RMSE%_C4_{suffix}"}
        )
        m = c3.merge(c4, on="Model")
        m[f"Delta_R2_{suffix}"] = m[f"R2_C4_{suffix}"] - m[f"R2_C3_{suffix}"]
        m[f"Delta_RMSE%_{suffix}"] = m[f"RMSE%_C4_{suffix}"] - m[f"RMSE%_C3_{suffix}"]
        return m[
            [
                "Model",
                f"R2_C3_{suffix}",
                f"R2_C4_{suffix}",
                f"Delta_R2_{suffix}",
                f"Delta_RMSE%_{suffix}",
            ]
        ]

    return _diff(df_wo, "wo").merge(_diff(df_w, "w"), on="Model")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rossmann Store Sales Forecasting Benchmark (Albassam et al., 2026)"
    )
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument(
        "--include-closed",
        action="store_true",
        help="Include closed stores (Open == 0) and zero-sales days.",
    )
    parser.add_argument(
        "--sample-stores",
        type=int,
        default=None,
        help="Optional store count limit for quick test runs.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Optional row limit (most recent rows) for quick test runs.",
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        default=CONFIGURATIONS,
        choices=CONFIGURATIONS,
        help="Configurations to run (default: C1 C2 C3 C4 C5).",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=None,
        help="Subset of model names to run (e.g., DecisionTree HistGradientBoosting XGBoost).",
    )
    parser.add_argument(
        "--scenarios",
        choices=["without", "with", "both"],
        default="both",
        help="Which customer ablation scenario(s) to run.",
    )
    parser.add_argument("--n-estimators", type=int, default=N_ESTIMATORS)
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=DEFAULT_N_JOBS,
        help="CPU threads for parallel models (default: 4 to prevent 16GB RAM swap).",
    )
    parser.add_argument("--cv-splits", type=int, default=N_SPLITS_CV)
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Ignore saved checkpoints and recompute selected experiments.",
    )
    parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Disable saving/loading checkpoints.",
    )
    parser.add_argument("--skip-cv", action="store_true")
    parser.add_argument("--skip-baselines", action="store_true")
    parser.add_argument("--skip-stats", action="store_true")
    parser.add_argument("--skip-sensitivity", action="store_true")
    parser.add_argument("--skip-shap", action="store_true")
    return parser.parse_args()


def _ensure_fitted_pipeline(
    pipes: dict,
    model_name: str,
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    include_customers: bool,
    n_estimators: int,
    n_jobs: int,
):
    """Refit C3 pipeline if it was resumed from checkpoint and needed for plots/SHAP."""
    if ("C3", model_name) in pipes:
        return pipes[("C3", model_name)]
    cols = get_feature_columns(df, config_name="C3", include_customers=include_customers)
    est = get_tree_models(n_estimators=n_estimators, random_state=RANDOM_STATE, n_jobs=n_jobs)[model_name]
    pipe = build_model_pipeline(train_df[cols], "C3", model_name, est)
    pipe.fit(train_df[cols], train_df[TARGET_COL].values)
    return pipe


def main() -> None:
    args = parse_args()
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ckpt_dir = None if args.no_checkpoint else CHECKPOINTS_DIR

    print("=== Stage 1: Loading and Preparing Rossmann Dataset ===")
    df = load_rossmann_data(
        data_dir=args.data_dir,
        filter_open_positive=not args.include_closed,
        sample_stores=args.sample_stores,
        max_rows=args.max_rows,
    )
    train_df, val_df = chronological_train_val_split(df, test_ratio=TEST_RATIO)
    print(
        f"Loaded {len(df):,} rows ({df['Store'].nunique()} stores) | "
        f"Train: {len(train_df):,} | Val: {len(val_df):,} "
        f"({val_df['Date'].nunique()} unique validation days)"
    )

    df_wo, preds_wo, pipes_wo = pd.DataFrame(), {}, {}
    df_w, preds_w, pipes_w = pd.DataFrame(), {}, {}

    # Stage 2A: Tree-based benchmark (Without Customers)
    if args.scenarios in ("without", "both"):
        print("\n=== Stage 2A: Tree-Based Models (Without Customers) ===")
        df_wo, preds_wo, pipes_wo = run_benchmark_suite(
            df=df,
            train_df=train_df,
            val_df=val_df,
            include_customers=False,
            configs=args.configs,
            model_names=args.models,
            n_estimators=args.n_estimators,
            n_jobs=args.n_jobs,
            n_splits=args.cv_splits,
            run_cv=not args.skip_cv,
            checkpoint_dir=ckpt_dir,
            force_rerun=args.force_rerun,
        )
        df_wo.to_csv(TABLES_DIR / "table4_rossmann_without_customers.csv", index=False)

    # Stage 2B: Tree-based benchmark (With Customers)
    if args.scenarios in ("with", "both"):
        print("\n=== Stage 2B: Tree-Based Models (With Customers) ===")
        df_w, preds_w, pipes_w = run_benchmark_suite(
            df=df,
            train_df=train_df,
            val_df=val_df,
            include_customers=True,
            configs=args.configs,
            model_names=args.models,
            n_estimators=args.n_estimators,
            n_jobs=args.n_jobs,
            n_splits=args.cv_splits,
            run_cv=not args.skip_cv,
            checkpoint_dir=ckpt_dir,
            force_rerun=args.force_rerun,
        )
        df_w.to_csv(TABLES_DIR / "table5_rossmann_with_customers.csv", index=False)

    # Ablation Summary Tables (Table 6 & Table 7)
    table6 = build_customer_ablation_table(df_wo, df_w)
    if not table6.empty:
        table6.to_csv(TABLES_DIR / "table6_customer_ablation_c3.csv", index=False)

    table7 = build_seasonality_ablation_table(df_wo, df_w)
    if not table7.empty:
        table7.to_csv(TABLES_DIR / "table7_seasonality_ablation_c3_vs_c4.csv", index=False)

    # Classical Forecasting Baselines (Table 8)
    baseline_preds = {}
    if not args.skip_baselines and not df_wo.empty and "C3" in df_wo["Config"].values:
        print("\n=== Stage 3: Classical Forecasting Baselines (C3, Without Customers) ===")
        df_base, baseline_preds = evaluate_classical_baselines(
            df=df,
            train_df=train_df,
            val_df=val_df,
            n_splits=args.cv_splits,
        )
        best_wo_row = (
            df_wo[df_wo["Config"] == "C3"]
            .sort_values("R2", ascending=False)
            .iloc[0]
        )
        best_tree_df = pd.DataFrame(
            [
                {
                    "Model": best_wo_row["Model"],
                    "RMSE": best_wo_row["RMSE"],
                    "RMSE%": best_wo_row["RMSE%"],
                    "MAE": best_wo_row["MAE"],
                    "R2": best_wo_row["R2"],
                    "CV_R2": best_wo_row["CV_R2"],
                    "CV_R2_Std": best_wo_row["CV_R2_Std"],
                }
            ]
        )
        table8 = pd.concat([df_base, best_tree_df], ignore_index=True)
        table8.to_csv(TABLES_DIR / "table8_classical_baselines_c3.csv", index=False)
        print(table8.to_string(index=False))

    # Diebold-Mariano Statistical Significance Tests (Table 10)
    if not args.skip_stats:
        print("\n=== Stage 4: Diebold-Mariano Tests (Newey-West HAC lag=7, Holm) ===")
        comparisons = []
        if ("C3", "RandomForest") in preds_wo and ("C3", "ExtraTrees") in preds_wo:
            comparisons.append(("RF vs. ET, Without Customers (top-2)", preds_wo[("C3", "RandomForest")], preds_wo[("C3", "ExtraTrees")]))
        if ("C3", "RandomForest") in preds_wo:
            if "Ridge Regression" in baseline_preds:
                comparisons.append(("RF vs. Ridge (baseline)", preds_wo[("C3", "RandomForest")], baseline_preds["Ridge Regression"]))
            if "Seasonal-Naive" in baseline_preds:
                comparisons.append(("RF vs. Seasonal-Naive (baseline)", preds_wo[("C3", "RandomForest")], baseline_preds["Seasonal-Naive"]))
            if "ETS" in baseline_preds:
                comparisons.append(("RF vs. ETS (baseline)", preds_wo[("C3", "RandomForest")], baseline_preds["ETS"]))
        if ("C1", "RandomForest") in preds_wo and ("C2", "RandomForest") in preds_wo:
            comparisons.append(("RF: C1 vs. C2 (preprocessing effect)", preds_wo[("C1", "RandomForest")], preds_wo[("C2", "RandomForest")]))
        if ("C2", "RandomForest") in preds_wo and ("C3", "RandomForest") in preds_wo:
            comparisons.append(("RF: C2 vs. C3 (zero-variance effect)", preds_wo[("C2", "RandomForest")], preds_wo[("C3", "RandomForest")]))
        if ("C3", "RandomForest") in preds_wo and ("C4", "RandomForest") in preds_wo:
            comparisons.append(("RF: C3 vs. C4 (seasonal/promotional ablation)", preds_wo[("C3", "RandomForest")], preds_wo[("C4", "RandomForest")]))
        if ("C3", "RandomForest") in preds_w and ("C3", "ExtraTrees") in preds_w:
            comparisons.append(("RF vs. ET, With Customers (ablation)", preds_w[("C3", "RandomForest")], preds_w[("C3", "ExtraTrees")]))

        if comparisons:
            table10 = run_diebold_mariano_suite(val_df, comparisons)
            table10.to_csv(TABLES_DIR / "table10_diebold_mariano_tests.csv", index=False)
            print(table10.to_string(index=False))
        else:
            print("[INFO] Skipping DM tests: required model predictions not yet in cache.")

    # Sensitivity Analysis (Table 12)
    if not args.skip_sensitivity:
        print("\n=== Stage 5: Sensitivity Analysis (C3, Without Customers) ===")
        table12 = run_sensitivity_analysis(
            df=df,
            train_df=train_df,
            val_df=val_df,
            n_splits=args.cv_splits,
            n_jobs=args.n_jobs,
            run_cv=not args.skip_cv,
        )
        table12.to_csv(TABLES_DIR / "table12_sensitivity_analysis.csv", index=False)
        print(table12.to_string(index=False))

    # Interpretability & Plots (Figures 3, 5, 6, 7, 8)
    print("\n=== Stage 6: Plots, Feature Importance, and SHAP ===")
    y_val = val_df[TARGET_COL].values

    if not df_wo.empty and "C3" in df_wo["Config"].values:
        best_wo_model = (
            df_wo[df_wo["Config"] == "C3"].sort_values("R2", ascending=False).iloc[0]["Model"]
        )
        if ("C3", best_wo_model) in preds_wo:
            plot_actual_vs_predicted(
                y_true=y_val,
                y_pred=preds_wo[("C3", best_wo_model)],
                title=f"Actual vs Predicted: Rossmann Without Customers (C3 - {best_wo_model})",
                save_path=FIGURES_DIR / "fig3a_actual_vs_pred_without_customers.png",
            )
            pipe_wo = _ensure_fitted_pipeline(
                pipes_wo, best_wo_model, df, train_df, False, args.n_estimators, args.n_jobs
            )
            imp_wo = plot_feature_importances(
                pipe=pipe_wo,
                title=f"Top Feature Importances: Without Customers (C3 - {best_wo_model})",
                save_path=FIGURES_DIR / "fig5_feature_importance_without_customers.png",
            )
            imp_wo.to_csv(TABLES_DIR / "feature_importance_without_customers.csv", index=False)

            if not args.skip_shap:
                cols_wo = get_feature_columns(df, config_name="C3", include_customers=False)
                shap_wo = run_shap_analysis(
                    pipe=pipe_wo,
                    X_val=val_df[cols_wo],
                    scenario_tag="without_customers",
                )
                if shap_wo is not None:
                    shap_wo["feature_shap"].to_csv(TABLES_DIR / "shap_features_without_customers.csv", index=False)
                    shap_wo["category_shap"].to_csv(TABLES_DIR / "shap_categories_without_customers.csv", index=False)

    if not df_w.empty and "C3" in df_w["Config"].values:
        best_w_model = (
            df_w[df_w["Config"] == "C3"].sort_values("R2", ascending=False).iloc[0]["Model"]
        )
        if ("C3", best_w_model) in preds_w:
            plot_actual_vs_predicted(
                y_true=y_val,
                y_pred=preds_w[("C3", best_w_model)],
                title=f"Actual vs Predicted: Rossmann With Customers (C3 - {best_w_model})",
                save_path=FIGURES_DIR / "fig3b_actual_vs_pred_with_customers.png",
            )
            pipe_w = _ensure_fitted_pipeline(
                pipes_w, best_w_model, df, train_df, True, args.n_estimators, args.n_jobs
            )
            imp_w = plot_feature_importances(
                pipe=pipe_w,
                title=f"Top Feature Importances: With Customers (C3 - {best_w_model})",
                save_path=FIGURES_DIR / "fig6_feature_importance_with_customers.png",
            )
            imp_w.to_csv(TABLES_DIR / "feature_importance_with_customers.csv", index=False)

            if not args.skip_shap:
                cols_w = get_feature_columns(df, config_name="C3", include_customers=True)
                shap_w = run_shap_analysis(
                    pipe=pipe_w,
                    X_val=val_df[cols_w],
                    scenario_tag="with_customers",
                )
                if shap_w is not None:
                    shap_w["feature_shap"].to_csv(TABLES_DIR / "shap_features_with_customers.csv", index=False)
                    shap_w["category_shap"].to_csv(TABLES_DIR / "shap_categories_with_customers.csv", index=False)

    print(f"\nDone! All tables saved to: {TABLES_DIR}")
    print(f"All figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
