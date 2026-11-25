"""Interpretability & visualization: Actual vs Predicted, Feature Importance, and SHAP."""

from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from .config import FIGURES_DIR, RANDOM_STATE, SHAP_SAMPLE_SIZE

try:
    import shap

    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


def get_pipeline_feature_names(pipe: Pipeline) -> List[str]:
    """Extract output feature names after ColumnTransformer and optional VarianceThreshold."""
    preproc = pipe.named_steps["preprocessor"]
    col_trans = preproc.named_steps["preprocess"]
    names = list(col_trans.get_feature_names_out())

    if "var_thresh" in preproc.named_steps:
        mask = preproc.named_steps["var_thresh"].get_support()
        names = [n for n, keep in zip(names, mask) if keep]

    return names


def map_rossmann_feature_category(feature_name: str) -> str:
    """Map individual (possibly one-hot encoded) Rossmann feature to paper's 5 categories."""
    name_low = feature_name.lower()
    if "customer" in name_low:
        return "Customer"
    if "promo" in name_low:
        return "Promotional"
    if "competition" in name_low:
        return "Competition"
    if any(k in name_low for k in ("date_", "dayofweek", "holiday")):
        return "Calendar/Temporal"
    return "Store"


def plot_actual_vs_predicted(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str,
    save_path: Path,
    max_points: int = 20000,
) -> None:
    """Plot Actual vs Predicted scatter plot with perfect prediction diagonal (Figure 3)."""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_STATE)
    if len(y_true) > max_points:
        idx = rng.choice(len(y_true), size=max_points, replace=False)
        yt, yp = y_true[idx], y_pred[idx]
    else:
        yt, yp = y_true, y_pred

    max_val = float(max(np.max(yt), np.max(yp))) * 1.02

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=150)
    ax.scatter(yt, yp, alpha=0.25, s=8, edgecolors="none")
    ax.plot([0, max_val], [0, max_val], "r--", linewidth=1.2, label="Perfect prediction")
    ax.set_xlabel("Actual Sales")
    ax.set_ylabel("Predicted Sales")
    ax.set_title(title)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def plot_feature_importances(
    pipe: Pipeline,
    title: str,
    save_path: Path,
    top_n: int = 10,
) -> pd.DataFrame:
    """Plot top-N conventional tree-based feature importances (Figures 5 & 6)."""
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model = pipe.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return pd.DataFrame()

    feature_names = get_pipeline_feature_names(pipe)
    importances = model.feature_importances_

    imp_df = (
        pd.DataFrame({"Feature": feature_names, "Importance": importances})
        .sort_values("Importance", ascending=False)
        .reset_index(drop=True)
    )
    top_df = imp_df.head(top_n).iloc[::-1]

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    ax.barh(top_df["Feature"], top_df["Importance"], color="#4C78A8")
    ax.set_xlabel("Importance")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)

    return imp_df


def run_shap_analysis(
    pipe: Pipeline,
    X_val: pd.DataFrame,
    scenario_tag: str,
    figures_dir: Path = FIGURES_DIR,
    sample_size: int = SHAP_SAMPLE_SIZE,
) -> Optional[Dict[str, pd.DataFrame]]:
    """Compute TreeExplainer SHAP values on 500 validation samples (Section 3.9 & 4.6)."""
    if not HAS_SHAP:
        print(
            f"[WARN] shap not installed; skipping SHAP analysis for {scenario_tag}. "
            "Install with: pip install shap"
        )
        return None

    figures_dir.mkdir(parents=True, exist_ok=True)
    preproc = pipe.named_steps["preprocessor"]
    model = pipe.named_steps["model"]
    feature_names = get_pipeline_feature_names(pipe)

    n = min(sample_size, len(X_val))
    X_sample_raw = X_val.sample(n=n, random_state=RANDOM_STATE)
    X_sample_trans = preproc.transform(X_sample_raw)
    X_sample_df = pd.DataFrame(X_sample_trans, columns=feature_names)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample_df)

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    total_shap = float(np.sum(mean_abs_shap)) or 1.0

    feature_shap_df = (
        pd.DataFrame(
            {
                "Feature": feature_names,
                "Mean_Abs_SHAP": mean_abs_shap,
                "Share_Pct": (mean_abs_shap / total_shap) * 100.0,
                "Category": [map_rossmann_feature_category(f) for f in feature_names],
            }
        )
        .sort_values("Mean_Abs_SHAP", ascending=False)
        .reset_index(drop=True)
    )

    category_shap_df = (
        feature_shap_df.groupby("Category", as_index=False)[["Mean_Abs_SHAP", "Share_Pct"]]
        .sum()
        .sort_values("Share_Pct", ascending=False)
        .reset_index(drop=True)
    )

    # SHAP Summary Plot (Figure 7)
    plt.figure(figsize=(8, 5), dpi=150)
    shap.summary_plot(shap_values, X_sample_df, max_display=10, show=False)
    plt.title(f"SHAP Summary ({scenario_tag})")
    plt.tight_layout()
    plt.savefig(figures_dir / f"shap_summary_{scenario_tag}.png")
    plt.close()

    # SHAP Dependence Plot for top feature (Figure 8)
    top_feature = feature_shap_df.iloc[0]["Feature"]
    plt.figure(figsize=(7, 5), dpi=150)
    shap.dependence_plot(top_feature, shap_values, X_sample_df, show=False)
    plt.title(f"SHAP Dependence: {top_feature} ({scenario_tag})")
    plt.tight_layout()
    plt.savefig(figures_dir / f"shap_dependence_{scenario_tag}.png")
    plt.close()

    return {
        "feature_shap": feature_shap_df,
        "category_shap": category_shap_df,
    }
