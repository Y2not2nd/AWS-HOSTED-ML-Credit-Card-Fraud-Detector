from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

DAG_ID = "credit_card_model_promotion"

with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ml", "promotion", "bentoml"],
) as dag:

    promote_model = KubernetesPodOperator(
        task_id="promote_best_model",

        # Same namespace as BentoML inference pods
        namespace="ml-inference",

        name="credit-card-model-promoter",
        random_name_suffix=True,

        # IRSA-enabled ServiceAccount with S3 write access
        service_account_name="model-promotion-sa",

        # Force in-cluster Kubernetes auth
        in_cluster=True,

        # Keep pod around for debugging if it fails
        is_delete_operator_pod=False,

        # Promotion image (already correct)
        image=(
            "581212334853.dkr.ecr.eu-west-1.amazonaws.com/"
            "yas-ml-inference:model-promoter-v4"
        ),
        image_pull_policy="Always",

        get_logs=True,
        log_events_on_failure=True,

        # Environment variables injected into the container
        env_vars={
            # MLflow
            "MLFLOW_TRACKING_URI": "http://mlflow.mlflow.svc.cluster.local:5000",

            # Bento model storage
            "BENTO_S3_BUCKET": "mlops-model-store-prod",
            "BENTO_S3_PREFIX": "bentoml/models",

            # 🔑 NEW: promotion target stage
            "BENTO_MODEL_STAGE": "CANDIDATE",

            # AWS region (IRSA handles auth)
            "AWS_REGION": "eu-west-1",
            "AWS_DEFAULT_REGION": "eu-west-1",
        },

        # Promotion script
        cmds=["python", "-u", "/app/promotion/build_bento.py"],
        arguments=[
            "--experiment-name",
            "credit_card_fraud_detection",
            "--metric-threshold",
            "0.95",
        ],

        retries=0,
    )
