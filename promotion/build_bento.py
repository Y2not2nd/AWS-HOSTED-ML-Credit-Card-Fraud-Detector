import mlflow
import joblib
import bentoml
import argparse
import os
import tempfile

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-name", required=True)
    parser.add_argument("--metric-threshold", type=float, required=True)
    args = parser.parse_args()

    client = mlflow.tracking.MlflowClient()
    exp = client.get_experiment_by_name(args.experiment_name)

    runs = client.search_runs(
        experiment_ids=[exp.experiment_id],
        order_by=["metrics.roc_auc DESC"],
        max_results=1,
    )

    best_run = runs[0]

    if best_run.data.metrics["roc_auc"] < args.metric_threshold:
        raise RuntimeError("Model does not meet promotion threshold")

    with tempfile.TemporaryDirectory() as tmp:
        model_path = client.download_artifacts(
            best_run.info.run_id,
            "model/model.joblib",
            dst_path=tmp,
        )

        model = joblib.load(model_path)

        bentoml.sklearn.save_model(
            name="credit_fraud_model",
            model=model,
            metadata={
                "run_id": best_run.info.run_id,
                "roc_auc": best_run.data.metrics["roc_auc"],
            },
        )

if __name__ == "__main__":
    main()
