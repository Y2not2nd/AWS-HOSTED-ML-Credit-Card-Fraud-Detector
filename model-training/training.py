import argparse
import json
import os
import sys

import pandas as pd
import mlflow
import mlflow.sklearn

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Train credit card fraud model with time-based splits")

    parser.add_argument(
        "--data-path",
        required=True,
        help="Path to full credit card CSV (local path or mounted S3 file)",
    )

    parser.add_argument(
        "--train-end-percent",
        type=float,
        required=True,
        help="Fraction of data to use for training, e.g. 0.6",
    )

    parser.add_argument(
        "--test-end-percent",
        type=float,
        required=True,
        help="Fraction of data to use for testing end, e.g. 0.7",
    )

    parser.add_argument(
        "--experiment-name",
        default="credit_card_fraud_detection",
        help="MLflow experiment name",
    )

    parser.add_argument(
        "--registered-model-name",
        default="credit_card_fraud_model",
        help="MLflow registered model name",
    )

    parser.add_argument(
        "--tracking-uri",
        default="",
        help="MLflow tracking URI (or set MLFLOW_TRACKING_URI env var)",
    )

    return parser.parse_args()


def validate_percentages(train_end: float, test_end: float):
    if not (0.0 < train_end < test_end <= 1.0):
        raise ValueError(
            "Percentages must satisfy: 0 < train_end < test_end <= 1.0"
        )


def load_and_slice_data(
    data_path: str, train_end: float, test_end: float
):
    df = pd.read_csv(data_path)

    if "Time" not in df.columns:
        raise ValueError("Dataset must contain a 'Time' column")

    if "Class" not in df.columns:
        raise ValueError("Dataset must contain a 'Class' column")

    # Sort chronologically
    df = df.sort_values("Time").reset_index(drop=True)

    n_rows = len(df)
    train_end_idx = int(n_rows * train_end)
    test_end_idx = int(n_rows * test_end)

    train_df = df.iloc[:train_end_idx]
    test_df = df.iloc[train_end_idx:test_end_idx]

    if train_df.empty or test_df.empty:
        raise ValueError("Train or test split resulted in empty dataset")

    return train_df, test_df


def build_pipeline():
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def main():
    args = parse_args()
    validate_percentages(args.train_end_percent, args.test_end_percent)

    tracking_uri = args.tracking_uri or os.getenv("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise RuntimeError(
            "MLflow tracking URI must be provided via --tracking-uri or MLFLOW_TRACKING_URI"
        )

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(args.experiment_name)

    train_df, test_df = load_and_slice_data(
        args.data_path,
        args.train_end_percent,
        args.test_end_percent,
    )

    X_train = train_df.drop(columns=["Class"])
    y_train = train_df["Class"]

    X_test = test_df.drop(columns=["Class"])
    y_test = test_df["Class"]

    pipeline = build_pipeline()

    with mlflow.start_run():
        mlflow.log_param("train_end_percent", args.train_end_percent)
        mlflow.log_param("test_end_percent", args.test_end_percent)
        mlflow.log_param("train_rows", len(train_df))
        mlflow.log_param("test_rows", len(test_df))

        pipeline.fit(X_train, y_train)

        y_pred_proba = pipeline.predict_proba(X_test)[:, 1]

        roc_auc = roc_auc_score(y_test, y_pred_proba)
        avg_precision = average_precision_score(y_test, y_pred_proba)

        mlflow.log_metric("roc_auc", roc_auc)
        mlflow.log_metric("average_precision", avg_precision)

        mlflow.sklearn.log_model(
            pipeline,
            artifact_path="model",
            registered_model_name=args.registered_model_name,
        )

        run_id = mlflow.active_run().info.run_id

    output = {
        "run_id": run_id,
        "metrics": {
            "roc_auc": roc_auc,
            "average_precision": avg_precision,
        },
        "data_split": {
            "train_end_percent": args.train_end_percent,
            "test_end_percent": args.test_end_percent,
            "train_rows": len(train_df),
            "test_rows": len(test_df),
        },
    }

    print(json.dumps(output))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
