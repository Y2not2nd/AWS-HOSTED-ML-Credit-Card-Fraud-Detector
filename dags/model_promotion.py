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

        # IMPORTANT: same namespace as BentoML inference pods
        namespace="ml-inference",

        name="credit-card-model-promoter",
        random_name_suffix=True,

        # IRSA-enabled ServiceAccount with S3 write access
        service_account_name="model-promotion-sa",

        # 🔑 CRITICAL FIX:
        # Force Airflow to use in-cluster Kubernetes credentials
        in_cluster=True,

        # Keep pod around if it fails so we can inspect logs
        is_delete_operator_pod=False,

        # Image that contains build_bento.py + deps
        image="581212334853.dkr.ecr.eu-west-1.amazonaws.com/yas-ml-inference:model-promoter",
        image_pull_policy="Always",

        get_logs=True,
        log_events_on_failure=True,

        # Inject BentoML S3 config
        env_vars={
            "BENTOML_CONFIG": "/config/bentoml.yaml",
        },

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

        cmds=["python", "-u", "/app/promotion/build_bento.py"],
        arguments=[
            "--experiment-name",
            "credit_card_fraud_detection",
            "--metric-threshold",
            "0.95",
        ],

        retries=0,
    )
