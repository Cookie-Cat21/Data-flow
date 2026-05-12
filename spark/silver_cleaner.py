"""
Spark batch job: Bronze → Silver Delta tables.

Reads from Bronze, applies:
  - column renaming / standardisation
  - type casting (strings → timestamps, decimals)
  - null filtering on mandatory keys
  - deduplication by natural key

Run on Databricks as a scheduled job after the streaming micro-batches settle.
"""

import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from dotenv import load_dotenv

load_dotenv()

BRONZE_BASE = os.getenv("DELTA_BRONZE_PATH", "dbfs:/dataflow/bronze")
SILVER_BASE = os.getenv("DELTA_SILVER_PATH", "dbfs:/dataflow/silver")


def create_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("dataflow-silver-cleaner")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )


def read_bronze(spark: SparkSession, table: str) -> DataFrame:
    return spark.read.format("delta").load(f"{BRONZE_BASE}/{table}")


def write_silver(df: DataFrame, table: str):
    (
        df.write
        .format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .save(f"{SILVER_BASE}/{table}")
    )
    print(f"[silver_cleaner] Written {df.count()} rows → silver/{table}")


# ── Per-table cleaning logic ──────────────────────────────────────────────────

def clean_orders(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "orders")
    return (
        df
        .filter(F.col("order_id").isNotNull())
        .filter(F.col("_corrupt_record").isNull() | F.col("_corrupt_record").isNotNull())  # keep all; mark corrupt
        .withColumn("order_purchase_ts", F.to_timestamp("order_purchase_timestamp"))
        .withColumn("order_approved_ts", F.to_timestamp("order_approved_at"))
        .withColumn("order_delivered_carrier_ts", F.to_timestamp("order_delivered_carrier_date"))
        .withColumn("order_delivered_customer_ts", F.to_timestamp("order_delivered_customer_date"))
        .withColumn("order_estimated_delivery_ts", F.to_timestamp("order_estimated_delivery_date"))
        .drop(
            "order_purchase_timestamp", "order_approved_at",
            "order_delivered_carrier_date", "order_delivered_customer_date",
            "order_estimated_delivery_date",
        )
        .dropDuplicates(["order_id"])
        .filter(F.col("order_purchase_ts").isNotNull())
    )


def clean_order_items(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "order_items")
    return (
        df
        .filter(F.col("order_id").isNotNull() & F.col("product_id").isNotNull())
        .withColumn("price", F.col("price").cast("decimal(10,2)"))
        .withColumn("freight_value", F.col("freight_value").cast("decimal(10,2)"))
        .withColumn("shipping_limit_ts", F.to_timestamp("shipping_limit_date"))
        .drop("shipping_limit_date")
        .dropDuplicates(["order_id", "order_item_id"])
    )


def clean_order_payments(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "order_payments")
    return (
        df
        .filter(F.col("order_id").isNotNull())
        .withColumn("payment_value", F.col("payment_value").cast("decimal(10,2)"))
        .dropDuplicates(["order_id", "payment_sequential"])
    )


def clean_order_reviews(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "order_reviews")
    return (
        df
        .filter(F.col("order_id").isNotNull())
        .withColumn("review_score", F.col("review_score").cast("int"))
        .filter(F.col("review_score").between(1, 5))
        .withColumn("review_creation_ts", F.to_timestamp("review_creation_date"))
        .drop("review_creation_date")
        .dropDuplicates(["review_id"])
    )


def clean_customers(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "customers")
    return (
        df
        .filter(F.col("customer_id").isNotNull())
        .withColumn("customer_state", F.upper("customer_state"))
        .withColumn("customer_city", F.initcap(F.lower("customer_city")))
        .dropDuplicates(["customer_id"])
    )


def clean_sellers(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "sellers")
    return (
        df
        .filter(F.col("seller_id").isNotNull())
        .withColumn("seller_state", F.upper("seller_state"))
        .withColumn("seller_city", F.initcap(F.lower("seller_city")))
        .dropDuplicates(["seller_id"])
    )


def clean_products(spark: SparkSession) -> DataFrame:
    df = read_bronze(spark, "products")
    return (
        df
        .filter(F.col("product_id").isNotNull())
        .withColumnRenamed("product_name_lenght", "product_name_length")
        .withColumnRenamed("product_description_lenght", "product_description_length")
        .dropDuplicates(["product_id"])
    )


# ── Main ─────────────────────────────────────────────────────────────────────

CLEANERS = {
    "orders": clean_orders,
    "order_items": clean_order_items,
    "order_payments": clean_order_payments,
    "order_reviews": clean_order_reviews,
    "customers": clean_customers,
    "sellers": clean_sellers,
    "products": clean_products,
}


def main():
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    for table, cleaner_fn in CLEANERS.items():
        try:
            print(f"[silver_cleaner] Processing {table}...")
            df = cleaner_fn(spark)
            write_silver(df, table)
        except Exception as e:
            print(f"[silver_cleaner] ERROR on {table}: {e}")
            raise

    print("[silver_cleaner] All tables written to Silver. Done.")


if __name__ == "__main__":
    main()
