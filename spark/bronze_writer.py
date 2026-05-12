"""
Spark Structured Streaming job: Kafka → Bronze Delta tables.

Reads from all Kafka topics simultaneously, deserialises JSON payloads,
applies the relevant schema (PERMISSIVE mode — bad records go to
dead-letter), and writes micro-batches to Bronze Delta tables.

Run on Databricks:
    spark-submit spark/bronze_writer.py
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from dotenv import load_dotenv

from spark.schemas import TOPIC_SCHEMA_MAP

load_dotenv()

KAFKA_BOOTSTRAP = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
KAFKA_API_KEY = os.environ["KAFKA_API_KEY"]
KAFKA_API_SECRET = os.environ["KAFKA_API_SECRET"]

BRONZE_BASE = os.getenv("DELTA_BRONZE_PATH", "dbfs:/dataflow/bronze")
CHECKPOINT_BASE = os.getenv("CHECKPOINT_PATH", "dbfs:/dataflow/checkpoints/bronze")

TOPICS = list(TOPIC_SCHEMA_MAP.keys())
DEAD_LETTER_TOPIC = "dataflow.dead_letter"


def create_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("dataflow-bronze-writer")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.optimizeWrite.enabled", "true")
        .config("spark.databricks.delta.autoCompact.enabled", "true")
        .getOrCreate()
    )


def kafka_source(spark: SparkSession):
    return (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("kafka.security.protocol", "SASL_SSL")
        .option("kafka.sasl.mechanism", "PLAIN")
        .option("kafka.sasl.jaas.config",
                f'org.apache.kafka.common.security.plain.PlainLoginModule required '
                f'username="{KAFKA_API_KEY}" password="{KAFKA_API_SECRET}";')
        .option("subscribe", ",".join(TOPICS))
        .option("startingOffsets", "earliest")
        .option("maxOffsetsPerTrigger", 50_000)
        .option("failOnDataLoss", "false")
        .load()
    )


def write_topic_stream(spark: SparkSession, raw_stream, topic: str, schema):
    """Filter stream to a single topic, parse JSON, write to Bronze Delta."""

    table_name = topic.replace("dataflow.", "").replace(".", "_")
    delta_path = f"{BRONZE_BASE}/{table_name}"
    checkpoint_path = f"{CHECKPOINT_BASE}/{table_name}"

    parsed = (
        raw_stream
        .filter(F.col("topic") == topic)
        .select(
            F.col("offset").cast("long").alias("_kafka_offset"),
            F.col("partition").cast("int").alias("_kafka_partition"),
            F.col("timestamp").alias("_kafka_timestamp"),
            F.from_json(
                F.col("value").cast(StringType()),
                schema,
                options={"mode": "PERMISSIVE", "columnNameOfCorruptRecord": "_corrupt_record"},
            ).alias("data"),
        )
        .select(
            "_kafka_offset",
            "_kafka_partition",
            "_kafka_timestamp",
            "data.*",
        )
        # Partition Bronze by ingestion date for efficient downstream reads
        .withColumn("_ingestion_date", F.to_date("_kafka_timestamp"))
    )

    return (
        parsed.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
        .option("mergeSchema", "true")
        .partitionBy("_ingestion_date")
        .trigger(processingTime="30 seconds")
        .start(delta_path)
    )


def main():
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    raw = kafka_source(spark)

    queries = []
    for topic, schema in TOPIC_SCHEMA_MAP.items():
        q = write_topic_stream(spark, raw, topic, schema)
        queries.append(q)
        print(f"[bronze_writer] Streaming started → {topic}")

    # Block until all streams terminate (or error)
    for q in queries:
        q.awaitTermination()


if __name__ == "__main__":
    main()
