import mlflow
import joblib
import bentoml
import argparse
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--metric-threshold", type=float, required=True)
    args = parser.parse_args()

    # Connect to MLflow
    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(args.experiment_name)

    if exp is None:
        raise RuntimeError(f"Experiment not found: {args.experiment_name}")

    # Get best run by ROC AUC
    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.roc_auc DESC"],
        max_results=1,
    )

    if not runs:
        raise RuntimeError("No runs found for experiment")

    best_run = runs[0]
    roc_auc = best_run.data.metrics.get("roc_auc")

    if roc_auc is None:
        raise RuntimeError("Best run does not contain roc_auc metric")

    if roc_auc < args.metric_threshold:
        raise RuntimeError(
            f"Model does not meet promotion threshold: {roc_auc} < {args.metric_threshold}"
        )

    # Download and load model artifact
    with tempfile.TemporaryDirectory() as tmp:
        model_path = client.download_artifacts(
            best_run.info.run_id,
            "model/model.joblib",
            dst_path=tmp,
        )

        model = joblib.load(model_path)

        # Save model to BentoML (using configured model store, S3)
        saved_model = bentoml.sklearn.save_model(
            name="credit_fraud_model",
            model=model,
            metadata={
                "run_id": best_run.info.run_id,
                "roc_auc": roc_auc,
            },
        )

        model_tag = str(saved_model.tag)

        # Explicitly push model to remote store (S3)
        bentoml.models.push(model_tag)

        # Log promoted model reference (critical for downstream inference)
        print(f"✅ Model promoted successfully")
        print(f"📦 BentoML model tag: {model_tag}")
        print(f"📈 ROC AUC: {roc_auc}")


if __name__ == "__main__":
    main()
