"""PySpark schema definitions for each Kafka topic payload."""

from pyspark.sql.types import (
    DecimalType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

ORDER_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("customer_id", StringType(), True),
    StructField("order_status", StringType(), True),
    StructField("order_purchase_timestamp", StringType(), True),
    StructField("order_approved_at", StringType(), True),
    StructField("order_delivered_carrier_date", StringType(), True),
    StructField("order_delivered_customer_date", StringType(), True),
    StructField("order_estimated_delivery_date", StringType(), True),
    StructField("purchase_timestamp", StringType(), True),   # replay metadata
    StructField("_event_type", StringType(), True),
])

ORDER_ITEM_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("order_item_id", IntegerType(), True),
    StructField("product_id", StringType(), True),
    StructField("seller_id", StringType(), True),
    StructField("shipping_limit_date", StringType(), True),
    StructField("price", DoubleType(), True),
    StructField("freight_value", DoubleType(), True),
    StructField("purchase_timestamp", StringType(), True),
    StructField("_event_type", StringType(), True),
])

ORDER_PAYMENT_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("payment_sequential", IntegerType(), True),
    StructField("payment_type", StringType(), True),
    StructField("payment_installments", IntegerType(), True),
    StructField("payment_value", DoubleType(), True),
    StructField("purchase_timestamp", StringType(), True),
    StructField("_event_type", StringType(), True),
])

ORDER_REVIEW_SCHEMA = StructType([
    StructField("review_id", StringType(), True),
    StructField("order_id", StringType(), False),
    StructField("review_score", IntegerType(), True),
    StructField("review_comment_title", StringType(), True),
    StructField("review_comment_message", StringType(), True),
    StructField("review_creation_date", StringType(), True),
    StructField("review_answer_timestamp", StringType(), True),
    StructField("purchase_timestamp", StringType(), True),
    StructField("_event_type", StringType(), True),
])

CUSTOMER_SCHEMA = StructType([
    StructField("customer_id", StringType(), False),
    StructField("customer_unique_id", StringType(), True),
    StructField("customer_zip_code_prefix", StringType(), True),
    StructField("customer_city", StringType(), True),
    StructField("customer_state", StringType(), True),
])

SELLER_SCHEMA = StructType([
    StructField("seller_id", StringType(), False),
    StructField("seller_zip_code_prefix", StringType(), True),
    StructField("seller_city", StringType(), True),
    StructField("seller_state", StringType(), True),
])

PRODUCT_SCHEMA = StructType([
    StructField("product_id", StringType(), False),
    StructField("product_category_name", StringType(), True),
    StructField("product_name_lenght", IntegerType(), True),
    StructField("product_description_lenght", IntegerType(), True),
    StructField("product_photos_qty", IntegerType(), True),
    StructField("product_weight_g", DoubleType(), True),
    StructField("product_length_cm", DoubleType(), True),
    StructField("product_height_cm", DoubleType(), True),
    StructField("product_width_cm", DoubleType(), True),
])

TOPIC_SCHEMA_MAP = {
    "dataflow.orders": ORDER_SCHEMA,
    "dataflow.order_items": ORDER_ITEM_SCHEMA,
    "dataflow.order_payments": ORDER_PAYMENT_SCHEMA,
    "dataflow.order_reviews": ORDER_REVIEW_SCHEMA,
    "dataflow.customers": CUSTOMER_SCHEMA,
    "dataflow.sellers": SELLER_SCHEMA,
    "dataflow.products": PRODUCT_SCHEMA,
}
