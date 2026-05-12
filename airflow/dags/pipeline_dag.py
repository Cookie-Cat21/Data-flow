"""
Main DataFlow pipeline DAG.

Schedule: every 6 hours.
Flow:
  start_replay  → wait_bronze_ready → run_silver_cleaner → trigger_dbt → refresh_dashboard

Uses DatabricksRunNowOperator to trigger pre-configured Databricks jobs
for the Spark steps, then kicks off the dbt Cosmos DAG.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.databricks.operators.databricks import (
    DatabricksRunNowOperator,
    DatabricksSubmitRunOperator,
)
from airflow.utils.task_group import TaskGroup

DEFAULT_ARGS = {
    "owner": "dataflow",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="dataflow_pipeline",
    description="End-to-end DataFlow pipeline: Kafka → Bronze → Silver → dbt Gold → Dashboard",
    schedule_interval="0 */6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["dataflow", "pipeline"],
) as dag:

    start = EmptyOperator(task_id="start")

    # ── Ingestion: trigger the Kafka producer job on Databricks ────────────
    with TaskGroup("ingestion") as ingestion_group:
        run_producer = DatabricksSubmitRunOperator(
            task_id="run_kafka_producer",
            databricks_conn_id="databricks_default",
            json={
                "run_name": "dataflow-kafka-producer",
                "existing_cluster_id": "{{ var.value.databricks_cluster_id }}",
                "spark_python_task": {
                    "python_file": "dbfs:/dataflow/scripts/producer.py",
                    "parameters": ["--speed", "100", "--batch-size", "50"],
                },
            },
        )

    # ── Bronze: wait for streaming to settle, then validate ───────────────
    with TaskGroup("bronze") as bronze_group:
        wait_for_streaming = EmptyOperator(
            task_id="wait_for_streaming_settle",
            # In production: replace with a Sensor that checks Delta table row count
        )

    # ── Silver: run the batch cleaner ─────────────────────────────────────
    with TaskGroup("silver") as silver_group:
        run_silver = DatabricksSubmitRunOperator(
            task_id="run_silver_cleaner",
            databricks_conn_id="databricks_default",
            json={
                "run_name": "dataflow-silver-cleaner",
                "existing_cluster_id": "{{ var.value.databricks_cluster_id }}",
                "spark_python_task": {
                    "python_file": "dbfs:/dataflow/scripts/silver_cleaner.py",
                },
            },
        )

    # ── Gold: trigger the dbt Cosmos DAG ──────────────────────────────────
    with TaskGroup("gold") as gold_group:
        trigger_dbt = TriggerDagRunOperator(
            task_id="trigger_dbt_dag",
            trigger_dag_id="dataflow_dbt",
            wait_for_completion=True,
            poke_interval=30,
        )

    # ── Dashboard: signal the WS server to reload ─────────────────────────
    with TaskGroup("serve") as serve_group:
        refresh_dashboard = EmptyOperator(
            task_id="signal_dashboard_refresh",
            # In production: call the WS server's /refresh endpoint via HttpOperator
        )

    end = EmptyOperator(task_id="end")

    # ── DAG dependency chain ───────────────────────────────────────────────
    start >> ingestion_group >> bronze_group >> silver_group >> gold_group >> serve_group >> end
