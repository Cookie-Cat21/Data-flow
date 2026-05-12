"""
dbt DAG via Astronomer Cosmos.

Cosmos auto-converts every dbt model into an Airflow task, giving you
per-model retries, lineage in the Airflow UI, and native dbt test tasks.

Triggered by the main pipeline_dag, but can also be run standalone
for dbt-only re-runs (e.g. after fixing a model).
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from cosmos import DbtDag, ProjectConfig, ProfileConfig, RenderConfig
from cosmos.profiles import DatabricksTokenProfileMapping

DBT_PROJECT_PATH = Path("/usr/local/airflow/dbt")
DBT_PROFILES_PATH = Path("/usr/local/airflow/dbt/profiles.yml")

profile_config = ProfileConfig(
    profile_name="dataflow",
    target_name="prod",
    profile_mapping=DatabricksTokenProfileMapping(
        conn_id="databricks_default",
        profile_args={
            "catalog": "hive_metastore",
            "schema": "dataflow",
        },
    ),
)

dbt_dag = DbtDag(
    dag_id="dataflow_dbt",
    project_config=ProjectConfig(DBT_PROJECT_PATH),
    profile_config=profile_config,
    render_config=RenderConfig(
        select=["path:models/staging", "path:models/intermediate", "path:models/marts", "path:models/reporting"],
        test_behavior="after_each",  # run dbt tests after each model
    ),
    schedule_interval=None,  # triggered externally by pipeline_dag
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        "owner": "dataflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=3),
    },
    tags=["dataflow", "dbt"],
)
