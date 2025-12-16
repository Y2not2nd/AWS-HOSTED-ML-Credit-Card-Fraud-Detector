from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="test_dag",
    start_date=datetime(2024, 2, 1),
    schedule=None,
    catchup=False,
) as dag:
    BashOperator(
        task_id="hello",
        bash_command="echo Hello from Airflow"
    )
