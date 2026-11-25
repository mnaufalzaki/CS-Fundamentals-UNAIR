"""Fold-safe preprocessing pipelines for Configurations C1 through C5."""

import re
from typing import List, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .config import (
    CUSTOMERS_COL,
    DATE_COL,
    SEASONAL_PROMO_REGEX,
    TARGET_COL,
)


def get_feature_columns(
    df: pd.DataFrame,
    config_name: str,
    include_customers: bool = False,
) -> List[str]:
    """Select feature columns according to configuration and customer ablation."""
    exclude_cols = {TARGET_COL, DATE_COL}
    if not include_customers:
        exclude_cols.add(CUSTOMERS_COL)

    feature_cols = [c for c in df.columns if c not in exclude_cols]

    # C4 and C5 exclude seasonal and promotional features via regex
    if config_name in ("C4", "C5"):
        pattern = re.compile(SEASONAL_PROMO_REGEX, flags=re.IGNORECASE)
        feature_cols = [c for c in feature_cols if not pattern.search(c)]

    return feature_cols


def split_feature_types(
    X: pd.DataFrame,
) -> Tuple[List[str], List[str]]:
    """Separate numerical and categorical feature column names."""
    cat_cols = X.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    num_cols = [c for c in X.columns if c not in cat_cols]
    return num_cols, cat_cols


def build_preprocessor(
    X: pd.DataFrame,
    config_name: str,
    allow_nan_passthrough: bool = True,
) -> Pipeline:
    """Build a fold-safe scikit-learn preprocessing pipeline for C1-C5.

    - C1 (Baseline): One-hot encoding of categoricals only; no imputation or
      zero-variance removal. If a downstream model cannot accept NaN values,
      set allow_nan_passthrough=False to avoid runtime crashes with a simple
      constant sentinel (-1) while still keeping C1 distinct from median/mode
      imputation in C2.
    - C2 (Preprocessed): Median imputation (numerical), mode imputation +
      one-hot encoding (categorical).
    - C3 (Preprocessed + Selected): C2 + VarianceThreshold(threshold=0.0).
    - C4 (Preprocessed, No Seasonality): Same pipeline as C2 (columns filtered).
    - C5 (Preprocessed + Selected, No Seasonality): Same pipeline as C3 (columns filtered).
    """
    num_cols, cat_cols = split_feature_types(X)

    if config_name == "C1":
        if allow_nan_passthrough:
            num_transformer = "passthrough"
        else:
            num_transformer = SimpleImputer(strategy="constant", fill_value=-1)

        cat_transformer = OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False,
        )
        col_transformer = ColumnTransformer(
            transformers=[
                ("num", num_transformer, num_cols),
                ("cat", cat_transformer, cat_cols),
            ],
            remainder="drop",
            verbose_feature_names_out=False,
        )
        return Pipeline(steps=[("preprocess", col_transformer)])

    # C2, C3, C4, C5: Full fold-safe preprocessing (median + mode + one-hot)
    num_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )
    cat_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    col_transformer = ColumnTransformer(
        transformers=[
            ("num", num_pipe, num_cols),
            ("cat", cat_pipe, cat_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    steps = [("preprocess", col_transformer)]

    # C3 and C5 add zero-variance feature removal
    if config_name in ("C3", "C5"):
        steps.append(("var_thresh", VarianceThreshold(threshold=0.0)))

    return Pipeline(steps=steps)
