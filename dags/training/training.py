import argparse
import json
import os
import sys
from urllib.parse import urlparse

import boto3
import pandas as pd
import mlflow

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train credit card fraud model with time-based splits"
    )

    parser.add_argument("--data-path", required=True)
    parser.add_argument("--train-end-percent", type=float, required=True)
    parser.add_argument("--test-end-percent", type=float, required=True)
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--tracking-uri", required=True)

    return parser.parse_args()


def validate_percentages(train_end: float, test_end: float):
    if not (0.0 < train_end < test_end <= 1.0):
        raise ValueError("Percentages must satisfy: 0 < train_end < test_end <= 1.0")


def resolve_data_path(data_path: str) -> str:
    if data_path.startswith("s3://"):
        parsed = urlparse(data_path)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        local_path = "/tmp/creditcard.csv"
        boto3.client("s3").download_file(bucket, key, local_path)
        return local_path

    return data_path


def load_and_slice_data(data_path: str, train_end: float, test_end: float):
    local_path = resolve_data_path(data_path)
    df = pd.read_csv(local_path)

    df = df.sort_values("Time").reset_index(drop=True)

    n_rows = len(df)
    train_end_idx = int(n_rows * train_end)
    test_end_idx = int(n_rows * test_end)

    train_df = df.iloc[:train_end_idx]
    test_df = df.iloc[train_end_idx:test_end_idx]

    return train_df, test_df


def build_pipeline():
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )


def main():
    args = parse_args()
    validate_percentages(args.train_end_percent, args.test_end_percent)

    mlflow.set_tracking_uri(args.tracking_uri)
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

    run_id = None
    try:
        with mlflow.start_run() as run:
            run_id = run.info.run_id

            mlflow.log_params(
                {
                    "train_end_percent": args.train_end_percent,
                    "test_end_percent": args.test_end_percent,
                    "train_rows": len(train_df),
                    "test_rows": len(test_df),
                }
            )

            pipeline.fit(X_train, y_train)

            y_pred_proba = pipeline.predict_proba(X_test)[:, 1]

            roc_auc = roc_auc_score(y_test, y_pred_proba)
            avg_precision = average_precision_score(y_test, y_pred_proba)

            mlflow.log_metric("roc_auc", roc_auc)
            mlflow.log_metric("average_precision", avg_precision)

            # SAFE: log model as plain artifact (no registry, no logged-models API)
            os.makedirs("/tmp/model", exist_ok=True)
            joblib.dump(pipeline, "/tmp/model/model.joblib")
            mlflow.log_artifact("/tmp/model/model.joblib", artifact_path="model")

        print(json.dumps({
            "run_id": run_id,
            "roc_auc": roc_auc,
            "average_precision": avg_precision,
        }))
        sys.stdout.flush()
        return 0

    except Exception as e:
        print(f"Training failed: {e}", file=sys.stderr)
        try:
            mlflow.end_run(status="FAILED")
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
