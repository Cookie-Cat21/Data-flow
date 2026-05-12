"""Kafka topic definitions and producer configuration."""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class TopicConfig:
    name: str
    partitions: int
    replication_factor: int
    retention_ms: int = 604_800_000  # 7 days


TOPICS: Dict[str, TopicConfig] = {
    "orders": TopicConfig("dataflow.orders", partitions=3, replication_factor=3),
    "order_items": TopicConfig("dataflow.order_items", partitions=3, replication_factor=3),
    "order_payments": TopicConfig("dataflow.order_payments", partitions=3, replication_factor=3),
    "order_reviews": TopicConfig("dataflow.order_reviews", partitions=3, replication_factor=3),
    "customers": TopicConfig("dataflow.customers", partitions=2, replication_factor=3),
    "sellers": TopicConfig("dataflow.sellers", partitions=2, replication_factor=3),
    "products": TopicConfig("dataflow.products", partitions=2, replication_factor=3),
    "dead_letter": TopicConfig("dataflow.dead_letter", partitions=1, replication_factor=3),
}


def get_producer_config(bootstrap_servers: str, api_key: str, api_secret: str) -> dict:
    return {
        "bootstrap.servers": bootstrap_servers,
        "security.protocol": "SASL_SSL",
        "sasl.mechanism": "PLAIN",
        "sasl.username": api_key,
        "sasl.password": api_secret,
        # Reliability settings
        "acks": "all",
        "enable.idempotence": True,
        "retries": 5,
        "retry.backoff.ms": 300,
        # Performance
        "linger.ms": 5,
        "batch.size": 16384,
        "compression.type": "snappy",
    }


def get_consumer_config(
    bootstrap_servers: str,
    api_key: str,
    api_secret: str,
    group_id: str,
) -> dict:
    return {
        "bootstrap.servers": bootstrap_servers,
        "security.protocol": "SASL_SSL",
        "sasl.mechanism": "PLAIN",
        "sasl.username": api_key,
        "sasl.password": api_secret,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "isolation.level": "read_committed",
    }
