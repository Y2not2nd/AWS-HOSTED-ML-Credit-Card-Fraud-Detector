import argparse
import os
import tempfile
from pathlib import Path
from datetime import datetime
import json
import joblib

import mlflow
from mlflow.tracking import MlflowClient
import bentoml
import boto3


def upload_directory_to_s3(local_dir: Path, bucket: str, prefix: str):
    """
    Recursively upload a directory to S3.
    """
    s3 = boto3.client("s3")

    for file_path in local_dir.rglob("*"):
        if file_path.is_file():
            s3_key = f"{prefix}/{file_path.relative_to(local_dir)}"
            s3.upload_file(
                Filename=str(file_path),
                Bucket=bucket,
                Key=s3_key,
            )


def write_candidate_pointer(
    bucket: str,
    prefix_base: str,
    model_name: str,
    tag: str,
    run_id: str,
    roc_auc: float,
):
    """
    Write a CANDIDATE pointer object to S3.
    """
    s3 = boto3.client("s3")

    pointer_key = f"{prefix_base}/CANDIDATE"

    payload = {
        "model": model_name,
        "tag": tag,
        "bento_s3_prefix": f"{prefix_base}/{tag}",
        "run_id": run_id,
        "roc_auc": roc_auc,
        "promoted_at": datetime.utcnow().isoformat() + "Z",
    }

    s3.put_object(
        Bucket=bucket,
        Key=pointer_key,
        Body=json.dumps(payload, indent=2),
        ContentType="application/json",
    )

    print(
        f"Wrote CANDIDATE pointer to "
        f"s3://{bucket}/{pointer_key}"
    )


def main():
    # ---------- ENV ----------
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise RuntimeError("MLFLOW_TRACKING_URI must be set")

    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

    s3_bucket = os.environ.get("BENTO_S3_BUCKET")
    if not s3_bucket:
        raise RuntimeError("BENTO_S3_BUCKET must be set")

    s3_prefix_base = os.environ.get(
        "BENTO_S3_PREFIX", "bentoml/models"
    )

    # ---------- ARGS ----------
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--metric-threshold", type=float, required=True)
    args = parser.parse_args()

    # ---------- GET EXP ----------
    exp = client.get_experiment_by_name(args.experiment_name)
    if not exp:
        raise RuntimeError(f"Experiment not found: {args.experiment_name}")

    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.roc_auc DESC"],
        max_results=1,
    )

    if not runs:
        raise RuntimeError("No runs found")

    best_run = runs[0]
    roc_auc = best_run.data.metrics.get("roc_auc")

    if roc_auc is None:
        raise RuntimeError("roc_auc metric missing")

    if roc_auc < args.metric_threshold:
        raise RuntimeError(
            f"Threshold not met: {roc_auc} < {args.metric_threshold}"
        )

    run_id = best_run.info.run_id
    print("Using run:", run_id)
    print("roc_auc:", roc_auc)

    # ---------- DOWNLOAD ARTIFACT ----------
    with tempfile.TemporaryDirectory() as tmp:
        local_path = client.download_artifacts(
            run_id=run_id,
            path="model/model.joblib",
            dst_path=tmp,
        )

        print("Downloaded model to:", local_path)

        model = joblib.load(local_path)

        # ---------- SAVE TO BENTOML (LOCAL ONLY) ----------
        saved = bentoml.sklearn.save_model(
            name="credit_fraud_model",
            model=model,
            metadata={
                "run_id": run_id,
                "roc_auc": roc_auc,
                "experiment": args.experiment_name,
            },
        )

        tag = str(saved.tag)
        print("Saved BentoML model:", tag)

        # ---------- LOCATE MODEL DIRECTORY ----------
        model_store = Path(saved.path)
        if not model_store.exists():
            raise RuntimeError("Saved BentoML model path not found")

        # ---------- UPLOAD TO S3 ----------
        s3_prefix = f"{s3_prefix_base}/{tag}"

        print(
            f"Uploading BentoML model to "
            f"s3://{s3_bucket}/{s3_prefix}"
        )

        upload_directory_to_s3(
            local_dir=model_store,
            bucket=s3_bucket,
            prefix=s3_prefix,
        )

        print("Upload complete")

        # ---------- WRITE CANDIDATE POINTER ----------
        write_candidate_pointer(
            bucket=s3_bucket,
            prefix_base=s3_prefix_base,
            model_name="credit_fraud_model",
            tag=tag,
            run_id=run_id,
            roc_auc=roc_auc,
        )

        print("Promotion finished successfully")


if __name__ == "__main__":
    main()
