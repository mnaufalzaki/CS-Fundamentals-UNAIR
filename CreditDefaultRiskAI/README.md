# Credit Default Risk AI

Credit Default Risk AI is a Streamlit-based machine learning dashboard for predicting next-month credit card default risk. The project compares a standard deep neural network with a hybrid PCA-DNN pipeline and provides an interactive interface for model evaluation, single-customer prediction, and prediction history tracking.

## Project Overview

The system predicts whether a credit card client is likely to default in the following month.

- `0` = Non-default
- `1` = Default

The dataset includes credit limits, demographic attributes, payment history, bill amounts, payment amounts, and default status.

## Methodology

This project compares two modeling pipelines:

1. **DNN / MLP**  
   A deep neural network trained on all preprocessed input features.

2. **Hybrid PCA-DNN**  
   Principal Component Analysis is used for feature extraction before the transformed features are passed into a DNN.

Experiments are evaluated across three train-test split scenarios:

- 80% train, 20% test
- 75% train, 25% test
- 70% train, 30% test

SMOTE is applied only to the training data after splitting and scaling to avoid data leakage.

## Repository Structure

```text
CreditDefaultRiskAI/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/default of credit card clients.csv
│   └── processed/
├── notebooks/
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── model_dnn.py
│   ├── model_pca_dnn.py
│   ├── train.py
│   ├── evaluate.py
│   ├── predict.py
│   ├── database.py
│   └── utils.py
├── models/
├── outputs/
├── database/
└── poster/
```

## Installation

Use Python 3.10 to 3.12 for TensorFlow compatibility.

```bash
pip install -r requirements.txt
```

## Train the Model

```bash
python src/train.py
```

Training generates the following artifacts:

- `models/best_model.keras`
- `models/scaler.pkl`
- `models/pca.pkl` when the best model uses PCA
- `models/model_metadata.json`
- `models/feature_columns.json`
- `outputs/tables/evaluation_results.csv`
- evaluation charts in `outputs/figures/`
- experiment summary in `outputs/reports/experiment_summary.md`

Generated model files, processed data, runtime databases, and charts are intentionally ignored by Git to keep the repository clean.

## Run the Dashboard

```bash
streamlit run app.py
```

Dashboard pages:

- Home
- Dataset
- Preprocessing
- Feature Extraction
- Model Evaluation
- Risk Prediction
- Prediction History

## Key Features

- Dataset summary and class distribution analysis.
- Preprocessing explanation with leakage-safe SMOTE usage.
- PCA explanation for the Hybrid PCA-DNN pipeline.
- Evaluation tables and charts across split scenarios.
- Full 23-feature prediction form based on the original dataset schema.
- Risk card with default probability and decision recommendation.
- SQLite-backed prediction history for dashboard sessions.

## Best Model Selection

The best model is selected automatically using the following priority order:

1. Highest F1-score
2. Highest default-class recall
3. Highest precision
4. Highest accuracy
5. Lower validation loss

This priority is used because credit default prediction is commonly affected by class imbalance, so accuracy alone is not a reliable decision metric.

## Dataset Notes

The CSV file is derived from the UCI Credit Card Default dataset. The converted CSV keeps the original Excel header row inside the data, so `src/data_loader.py` automatically:

- uses the `ID, LIMIT_BAL, ..., default payment next month` row as the logical column header,
- removes the `ID` column,
- renames the target column to `default_status`,
- converts all feature columns into numeric values.

## Tech Stack

- Python
- Streamlit
- TensorFlow / Keras
- scikit-learn
- imbalanced-learn
- Plotly
- SQLite
