from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator

DAG_ID = "credit_card_fraud_training"

with DAG(
    dag_id=DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ml", "training", "credit-card"],
) as dag:

    train_model = KubernetesPodOperator(
        task_id="train_model",

        namespace="airflow",
        name="credit-card-training",
        random_name_suffix=True,

        service_account_name="credit-card-trainer",

        image="581212334853.dkr.ecr.eu-west-1.amazonaws.com/yas-ml-inference@sha256:b42926ba9bf233e233f393d51596b2e7aa3dbfba7b604fec70acd51823ad162d",
        image_pull_policy="Always",

        get_logs=True,
        log_events_on_failure=True,
        log_pod_spec_on_failure=True,

        on_finish_action="keep_pod",

        retries=0,
        deferrable=False,
        do_xcom_push=False,

        labels={
            "app": "credit-card-training",
            "dag_id": DAG_ID,
            "task": "train_model",
        },

        cmds=["python", "-u", "/app/training.py"],
        arguments=[
            "--data-path",
            "s3://bin2ml-ml-data-eu-west-1/credit-card-fraud/raw/creditcard.csv",
            "--train-end-percent",
            "0.6",
            "--test-end-percent",
            "0.8",
            "--experiment-name",
            "credit_card_fraud_detection",
            "--tracking-uri",
            "http://mlflow.mlflow.svc.cluster.local:5000",
        ],

        startup_timeout_seconds=300,
    )
