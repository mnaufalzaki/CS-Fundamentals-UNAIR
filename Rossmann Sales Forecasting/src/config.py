"""Configuration constants matching Albassam et al. (2026) methodology."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"
CHECKPOINTS_DIR = OUTPUT_DIR / "checkpoints"

RANDOM_STATE = 42
N_ESTIMATORS = 100
DT_MAX_DEPTH = 10
GB_PATIENCE = 10
DEFAULT_N_JOBS = 4
TEST_RATIO = 0.20
N_SPLITS_CV = 5
SHAP_SAMPLE_SIZE = 500
DM_HAC_LAG = 7

# Regex pattern for seasonal and promotional feature exclusion (C4 & C5)
SEASONAL_PROMO_REGEX = r"(holiday|weather|temp|season|weekend|quarter|weekday|promo)"

CONFIGURATIONS = ["C1", "C2", "C3", "C4", "C5"]

CONFIG_LABELS = {
    "C1": "C1: Baseline",
    "C2": "C2: Preprocessed",
    "C3": "C3: Preprocessed + Selected",
    "C4": "C4: Preprocessed, No Seasonality",
    "C5": "C5: Preprocessed + Selected, No Seasonality",
}

TARGET_COL = "Sales"
DATE_COL = "Date"
STORE_COL = "Store"
CUSTOMERS_COL = "Customers"
