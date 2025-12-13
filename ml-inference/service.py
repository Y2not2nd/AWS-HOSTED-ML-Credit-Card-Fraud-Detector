import os
import bentoml
import pandas as pd
from bentoml.io import PandasDataFrame, JSON
import numpy as np


# =========================
# Schema definition
# =========================
EXPECTED_FEATURE_COLUMNS = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]


# =========================
# Risk thresholds
# =========================
LOW_RISK_THRESHOLD = 0.7
HIGH_RISK_THRESHOLD = 0.9


# =========================
# Validation helpers
# =========================
def validate_input_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Input data is empty. Please upload a CSV with at least one row.")

    if "Class" in df.columns:
        df = df.drop(columns=["Class"])

    missing = set(EXPECTED_FEATURE_COLUMNS) - set(df.columns)
    extra = set(df.columns) - set(EXPECTED_FEATURE_COLUMNS)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if extra:
        raise ValueError(f"Unexpected columns detected: {sorted(extra)}")

    if df.select_dtypes(exclude=["number"]).columns.tolist():
        raise ValueError("All input features must be numeric.")

    if df.isnull().any().any():
        raise ValueError("Input contains NaN values.")

    return df


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    min_s, max_s = scores.min(), scores.max()
    if min_s == max_s:
        return np.zeros_like(scores)
    return (scores - min_s) / (max_s - min_s)


def assign_risk_level(score: float) -> str:
    if score >= HIGH_RISK_THRESHOLD:
        return "high"
    elif score >= LOW_RISK_THRESHOLD:
        return "medium"
    else:
        return "low"


# =========================
# Load model runner (UPDATED)
# =========================
MODEL_REF = os.environ.get(
    "BENTOML_MODEL_REF",
    "credit_card_fraud_classifier:latest",  # safe fallback
)

model_runner = bentoml.sklearn.get(MODEL_REF).to_runner()


# =========================
# Create service
# =========================
svc = bentoml.Service(
    name="credit_card_fraud_service",
    runners=[model_runner],
)


# =========================
# Prediction API
# =========================
@svc.api(
    input=PandasDataFrame(),
    output=JSON(),
)
def predict(data: pd.DataFrame):
    try:
        validated_data = validate_input_dataframe(data)

        raw_scores = model_runner.predict.run(validated_data)
        scores = normalize_scores(np.array(raw_scores))

        results = []

        for score in scores:
            risk_level = assign_risk_level(float(score))

            if risk_level == "high":
                decision = "flag_for_review"
            elif risk_level == "medium":
                decision = "review_if_capacity"
            else:
                decision = "allow"

            results.append(
                {
                    "fraud_probability": float(score),
                    "risk_level": risk_level,
                    "decision": decision,
                }
            )

        return {
            "status": "success",
            "results": results,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
        }
