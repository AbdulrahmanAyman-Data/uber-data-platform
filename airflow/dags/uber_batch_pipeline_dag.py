"""
airflow/dags/batch_pipeline_dag.py

Orchestrates the batch pipeline:
Bronze -> Silver -> Gold -> Hive Metastore refresh.

NiFi ingestion is run manually/out-of-band for the historical load,
so this DAG starts at the Spark layer and assumes Bronze data is already
present on HDFS.
"""

from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


SPARK_ENV_VARS = {"HADOOP_USER_NAME": "hdfs"}

TRINO_HOST = "uber-trino"
TRINO_PORT = 8080
TRINO_CATALOG = "hive"
TRINO_SCHEMA = "default"

PARTITIONED_GOLD_TABLES = [
    "fact_rides",
]
SQL_FILE = "/opt/airflow/sql/hive_ddl/star_schema_tables.sql"
def create_gold_tables():
    """Execute star_schema_tables.sql to create Gold tables in Hive Metastore (idempotent via IF NOT EXISTS)."""
    import trino

    with open(SQL_FILE, "r") as f:
        sql_content = f.read()

    # Split on ';' and drop empty/whitespace-only statements (e.g. trailing text after the last ';')
    statements = [
        stmt.strip()
        for stmt in sql_content.split(";")
        if stmt.strip()
    ]

    conn = trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user="airflow",
        catalog=TRINO_CATALOG,
        schema=TRINO_SCHEMA,
    )

    cursor = conn.cursor()

    for stmt in statements:
        cursor.execute(stmt)
        cursor.fetchall()
        print(f"[create_gold_tables] executed:\n{stmt[:80]}...")

    print("[create_gold_tables] all statements executed successfully.")

default_args = {
    "owner": "data-engineering",
    "retries": 1,
}


def refresh_hive_metastore_partitions():
    """Re-sync partition metadata for partitioned Gold tables after a fresh write."""
    import trino

    conn = trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user="airflow",
        catalog=TRINO_CATALOG,
        schema=TRINO_SCHEMA,
    )

    cursor = conn.cursor()

    for table in PARTITIONED_GOLD_TABLES:
        cursor.execute(
            f"CALL {TRINO_CATALOG}.system.sync_partition_metadata"
            f"('{TRINO_SCHEMA}', '{table}', 'FULL')"
        )
        cursor.fetchall()
        print(f"[refresh_hive_metastore_partitions] synced {table}")


with DAG(
    dag_id="uber_batch_pipeline_dag",
    description="Bronze -> Silver -> Gold -> Hive Metastore refresh",
    default_args=default_args,
    schedule="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["uber", "batch"],
) as dag:

    bronze_to_silver = SparkSubmitOperator(
        task_id="bronze_to_silver_rides",
        application="/opt/airflow/batch/bronze_to_silver_rides.py",
        conn_id="spark_default",
        env_vars=SPARK_ENV_VARS,
    )

    silver_to_gold = SparkSubmitOperator(
        task_id="silver_to_gold_rides",
        application="/opt/airflow/batch/silver_to_gold_rides.py",
        conn_id="spark_default",
        env_vars=SPARK_ENV_VARS,
    )

    create_gold_tables_task = PythonOperator(
        task_id="create_gold_tables",
        python_callable=create_gold_tables,
    )

    refresh_partitions = PythonOperator(
        task_id="refresh_hive_metastore_partitions",
        python_callable=refresh_hive_metastore_partitions,
    )

    bronze_to_silver >> silver_to_gold >> create_gold_tables_task >> refresh_partitions
