"""Data loading and chronological preparation for the Rossmann Store Sales dataset."""

from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from .config import DATE_COL, DATA_DIR, STORE_COL, TARGET_COL


def load_rossmann_data(
    data_dir: Path = DATA_DIR,
    filter_open_positive: bool = True,
    sample_stores: Optional[int] = None,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """Load and merge Rossmann train.csv and store.csv sorted chronologically.

    Args:
        data_dir: Directory containing train.csv and store.csv.
        filter_open_positive: If True, keep only open store days with Sales > 0.
        sample_stores: Optional limit on number of stores (useful for quick smoke tests).
        max_rows: Optional limit on total rows (takes most recent rows after sorting).

    Returns:
        Merged and chronologically sorted DataFrame with extracted date features.
    """
    train_path = Path(data_dir) / "train.csv"
    store_path = Path(data_dir) / "store.csv"

    if not train_path.exists() or not store_path.exists():
        raise FileNotFoundError(
            f"Expected train.csv and store.csv in {data_dir}."
        )

    # The supplied CSVs use ';'; original Kaggle CSVs use ','.
    def read_csv(path: Path) -> pd.DataFrame:
        with path.open(encoding="utf-8-sig") as source:
            header = source.readline()
        separator = ";" if header.count(";") > header.count(",") else ","
        return pd.read_csv(path, sep=separator, low_memory=False)

    train_df = read_csv(train_path)
    store_df = read_csv(store_path)

    # Merge historical sales with store metadata on Store identifier
    df = train_df.merge(store_df, on=STORE_COL, how="left")

    # Normalize mixed-type StateHoliday column ('0' vs 0)
    if "StateHoliday" in df.columns:
        df["StateHoliday"] = df["StateHoliday"].astype(str)

    # Parse Date and sort chronologically (with Store as deterministic tie-breaker)
    date_sample = str(df[DATE_COL].iloc[0])
    date_format = "%d/%m/%Y" if "/" in date_sample else "%Y-%m-%d"
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], format=date_format, errors="raise")
    df = df.sort_values([DATE_COL, STORE_COL]).reset_index(drop=True)

    # Project choice: evaluate sales on operational days with positive sales.
    if filter_open_positive:
        df = df[(df["Open"] == 1) & (df[TARGET_COL] > 0)].reset_index(drop=True)

    if sample_stores is not None:
        selected_stores = sorted(df[STORE_COL].unique())[:sample_stores]
        df = df[df[STORE_COL].isin(selected_stores)].reset_index(drop=True)

    if max_rows is not None and len(df) > max_rows:
        df = df.iloc[-max_rows:].reset_index(drop=True)

    # Extract calendar components from Date (matches paper's Date_Month, Date_Day features)
    df["Date_Year"] = df[DATE_COL].dt.year
    df["Date_Month"] = df[DATE_COL].dt.month
    df["Date_Day"] = df[DATE_COL].dt.day

    return df


def chronological_train_val_split(
    df: pd.DataFrame,
    test_ratio: float = 0.20,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split approximately 80/20 without placing the same date on both sides."""
    if not 0 < test_ratio < 1 or len(df) < 2:
        raise ValueError("test_ratio must be between 0 and 1, with at least two rows.")
    split_idx = int(len(df) * (1.0 - test_ratio))
    cutoff_date = df.iloc[split_idx][DATE_COL]
    split_idx = int(df[DATE_COL].searchsorted(cutoff_date, side="left"))
    if split_idx == 0:
        raise ValueError("Insufficient unique dates for a chronological split.")
    train_df = df.iloc[:split_idx].copy().reset_index(drop=True)
    val_df = df.iloc[split_idx:].copy().reset_index(drop=True)
    return train_df, val_df
