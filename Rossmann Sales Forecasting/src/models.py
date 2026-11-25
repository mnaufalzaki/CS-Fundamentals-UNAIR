"""Seven tree-based machine learning models configured per Albassam et al. (2026)."""

from typing import Dict

from sklearn.base import BaseEstimator
from sklearn.ensemble import (
    AdaBoostRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor

from .config import DT_MAX_DEPTH, GB_PATIENCE, N_ESTIMATORS, RANDOM_STATE

# Models that natively support missing values (NaN) in C1 Baseline
NAN_SAFE_MODELS = {
    "RandomForest",
    "ExtraTrees",
    "DecisionTree",
    "HistGradientBoosting",
    "XGBoost",
}


def get_tree_models(
    n_estimators: int = N_ESTIMATORS,
    random_state: int = RANDOM_STATE,
    n_jobs: int = -1,
) -> Dict[str, BaseEstimator]:
    """Return the 7 tree-based models with consistent controlled hyperparameters."""
    return {
        "AdaBoost": AdaBoostRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
        ),
        "DecisionTree": DecisionTreeRegressor(
            max_depth=DT_MAX_DEPTH,
            random_state=random_state,
        ),
        "ExtraTrees": ExtraTreesRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=n_jobs,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=n_estimators,
            n_iter_no_change=GB_PATIENCE,
            random_state=random_state,
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=n_estimators,
            random_state=random_state,
        ),
        "RandomForest": RandomForestRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=n_jobs,
        ),
        "XGBoost": XGBRegressor(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=n_jobs,
            verbosity=0,
        ),
    }
