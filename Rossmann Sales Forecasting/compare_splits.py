"""Compare chronological 70:30, 80:20 and 90:10 Random Forest splits.

Run from the project folder:
    python compare_splits.py
    python compare_splits.py --sample-stores 25 --n-estimators 20
"""

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

from src.config import DATA_DIR, OUTPUT_DIR, RANDOM_STATE, TARGET_COL
from src.data_loader import chronological_train_val_split, load_rossmann_data
from src.metrics import compute_metrics
from src.preprocessing import build_preprocessor, get_feature_columns


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--sample-stores", type=int, default=None,
                        help="Use a small subset for a quick check; report it as a subset.")
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--n-jobs", type=int, default=4)
    parser.add_argument("--include-customers", action="store_true")
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR / "split_comparison")
    return parser.parse_args()


def evaluate_splits(df, n_estimators=100, n_jobs=4, include_customers=False):
    """Return per-split training/testing results and a small plot sample."""
    cols = get_feature_columns(df, config_name="C3", include_customers=include_customers)
    rows, plot_samples = [], {}

    for train_fraction in (0.70, 0.80, 0.90):
        train, test = chronological_train_val_split(df, test_ratio=1 - train_fraction)
        assert train["Date"].max() < test["Date"].min()
        x_train, x_test = train[cols], test[cols]
        y_train, y_test = train[TARGET_COL].to_numpy(), test[TARGET_COL].to_numpy()

        model = Pipeline([
            ("preprocessor", build_preprocessor(x_train, config_name="C3")),
            ("model", RandomForestRegressor(
                n_estimators=n_estimators, random_state=RANDOM_STATE, n_jobs=n_jobs
            )),
        ])
        train_pct = round(train_fraction * 100)
        test_pct = 100 - train_pct
        print(f"Training {train_pct}:{test_pct} "
              f"({len(train):,} train / {len(test):,} test)...", flush=True)
        model.fit(x_train, y_train)
        predicted_train = model.predict(x_train)
        predicted_test = model.predict(x_test)
        train_metrics = compute_metrics(y_train, predicted_train, float(y_train.mean()))
        test_metrics = compute_metrics(y_test, predicted_test, float(y_train.mean()))
        label = f"{train_pct}:{test_pct}"

        for phase, part, metric in [
            ("Training", train, train_metrics), ("Testing", test, test_metrics)
        ]:
            rows.append({
                "Split": label, "Dataset": phase, "Records": len(part),
                "First_Date": part["Date"].min().date().isoformat(),
                "Last_Date": part["Date"].max().date().isoformat(),
                "Store_Count": int(part["Store"].nunique()),
                "Actual_Percent": 100 * len(part) / len(df),
                "N_Estimators": n_estimators,
                "Customers_Used": include_customers,
                **metric,
            })

        rng = np.random.default_rng(RANDOM_STATE)
        sample_idx = rng.choice(len(test), min(5000, len(test)), replace=False)
        plot_samples[label] = (y_test[sample_idx], predicted_test[sample_idx])
        print(f"  Train R2={train_metrics['R2']:.4f}; "
              f"Test R2={test_metrics['R2']:.4f}; "
              f"Test RMSE={test_metrics['RMSE']:.2f}", flush=True)

    results = pd.DataFrame(rows)
    train_results = results[results["Dataset"] == "Training"].set_index("Split")
    test_results = results[results["Dataset"] == "Testing"].set_index("Split")
    gaps = pd.DataFrame({
        "Split": train_results.index,
        "R2_Train_Minus_Test": train_results["R2"].to_numpy() - test_results["R2"].to_numpy(),
        "RMSE_Test_Minus_Train": test_results["RMSE"].to_numpy() - train_results["RMSE"].to_numpy(),
    })
    return results, gaps, plot_samples


def save_plots(results, plot_samples, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"Training": "#12427c", "Testing": "#f59e0b"}
    for metric in ("R2", "RMSE", "MAE"):
        wide = results.pivot(index="Split", columns="Dataset", values=metric)
        ax = wide[["Training", "Testing"]].plot.bar(
            figsize=(8, 5), color=[colors["Training"], colors["Testing"]], rot=0
        )
        ax.set(title=f"Random Forest: {metric} by chronological split",
               xlabel="Training : Testing ratio", ylabel=metric)
        ax.legend(title="")
        ax.figure.tight_layout()
        ax.figure.savefig(out_dir / f"comparison_{metric.lower()}.png", dpi=180)
        plt.close(ax.figure)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharex=True, sharey=True)
    all_values = np.concatenate([v for pair in plot_samples.values() for v in pair])
    limit = float(all_values.max()) * 1.02
    for ax, (label, (actual, predicted)) in zip(axes, plot_samples.items()):
        ax.scatter(actual, predicted, s=6, alpha=0.2, color="#256cae")
        ax.plot([0, limit], [0, limit], "r--", linewidth=1)
        ax.set(title=f"Split {label}", xlabel="Actual Sales", xlim=(0, limit), ylim=(0, limit))
    axes[0].set_ylabel("Predicted Sales")
    fig.tight_layout()
    fig.savefig(out_dir / "actual_vs_predicted_by_split.png", dpi=180)
    plt.close(fig)


def main():
    args = parse_args()
    if args.n_estimators < 1 or args.n_jobs == 0:
        raise ValueError("n-estimators must be positive and n-jobs cannot be zero.")
    df = load_rossmann_data(
        data_dir=args.data_dir, filter_open_positive=not args.include_closed,
        sample_stores=args.sample_stores,
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scope = f"{args.sample_stores}_stores" if args.sample_stores else "full_data"
    out_dir = args.output_dir / f"{stamp}_{scope}_{args.n_estimators}_trees"
    out_dir.mkdir(parents=True, exist_ok=False)

    results, gaps, plot_samples = evaluate_splits(
        df, n_estimators=args.n_estimators, n_jobs=args.n_jobs,
        include_customers=args.include_customers,
    )
    results.to_csv(out_dir / "train_test_metrics.csv", index=False)
    gaps.to_csv(out_dir / "generalization_gaps.csv", index=False)
    if not args.skip_plots:
        save_plots(results, plot_samples, out_dir)
    print("\nResults saved to:", out_dir.resolve())
    print("The testing periods differ across ratios; compare generalization, "
          "not a universal 'best split'.")


if __name__ == "__main__":
    main()
