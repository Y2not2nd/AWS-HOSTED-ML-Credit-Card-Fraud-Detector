import argparse
import os
import tempfile
import joblib

import mlflow
from mlflow.tracking import MlflowClient
import bentoml


def main():
    # ---------- ENV ----------
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise RuntimeError("MLFLOW_TRACKING_URI must be set")

    mlflow.set_tracking_uri(tracking_uri)
    client = MlflowClient()

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

        # ---------- SAVE TO BENTOML ----------
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

        # ---------- PUSH TO S3 ----------
        bentoml.models.push(tag)
        print("Model pushed to S3")


if __name__ == "__main__":
    main()
