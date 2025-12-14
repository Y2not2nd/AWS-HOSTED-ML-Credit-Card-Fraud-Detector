from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import V1Volume, V1ConfigMapVolumeSource, V1VolumeMount

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

        # 🔒 DIGEST-PINNED promotion image (NO TAG RESOLUTION)
        image=(
            "581212334853.dkr.ecr.eu-west-1.amazonaws.com/"
            "yas-ml-inference@sha256:"
            "d7b756617d9e7ef1bfb059299e9e87d7aa8de59a111837df86d72224e94929f0"
        ),
        image_pull_policy="Always",

        get_logs=True,
        log_events_on_failure=True,

        # Environment variables injected into the container
        env_vars={
            "BENTOML_CONFIG": "/config/bentoml.yaml",
            "BENTOML_HOME": "/tmp/bentoml",
            "MLFLOW_TRACKING_URI": "http://mlflow.mlflow.svc.cluster.local:5000",
        },

        # Mount BentoML config from ConfigMap
        volumes=[
            V1Volume(
                name="bentoml-config",
                config_map=V1ConfigMapVolumeSource(
                    name="bentoml-s3-config"
                ),
            )
        ],

        volume_mounts=[
            V1VolumeMount(
                name="bentoml-config",
                mount_path="/config",
                read_only=True,
            )
        ],

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
