"""
Kafka replay producer for the Olist dataset.

Reads CSVs in chronological order (by purchase_timestamp) and publishes
events to Kafka topics at a configurable speed multiplier, simulating
a live e-commerce event stream.

Usage:
    python -m ingestion.producer --speed 100 --batch-size 50
    python -m ingestion.producer --dry-run          # prints events, no Kafka
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

import pandas as pd
import yaml
from confluent_kafka import Producer, KafkaException
from dotenv import load_dotenv

from ingestion.topics import TOPICS, get_producer_config

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def load_config(path: str = "ingestion/config.yaml") -> dict:
    with open(path) as f:
        raw = f.read()
    # simple env var substitution
    for key, val in os.environ.items():
        raw = raw.replace(f"${{{key}}}", val)
    return yaml.safe_load(raw)


def load_olist(cfg: dict) -> dict[str, pd.DataFrame]:
    """Load all Olist CSVs into DataFrames."""
    base = Path(cfg["data"]["olist_dir"])
    files = cfg["data"]["files"]
    dfs = {}
    for name, filename in files.items():
        path = base / filename
        if not path.exists():
            log.warning("Missing file: %s — skipping", path)
            continue
        dfs[name] = pd.read_csv(path)
        log.info("Loaded %s: %d rows", name, len(dfs[name]))
    return dfs


def build_order_events(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge order-related tables and sort by purchase_timestamp to
    produce a unified, chronologically ordered event stream.
    """
    orders = dfs["orders"].copy()
    orders["purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
    orders = orders.sort_values("purchase_timestamp").reset_index(drop=True)

    items = dfs.get("order_items", pd.DataFrame())
    payments = dfs.get("order_payments", pd.DataFrame())
    reviews = dfs.get("order_reviews", pd.DataFrame())

    # tag each row with its event type and target topic
    event_frames = []

    orders["_event_type"] = "order_created"
    orders["_topic"] = TOPICS["orders"].name
    orders["_key"] = orders["order_id"]
    event_frames.append(orders)

    if not items.empty:
        items["purchase_timestamp"] = items["order_id"].map(
            orders.set_index("order_id")["purchase_timestamp"]
        )
        items["_event_type"] = "order_item"
        items["_topic"] = TOPICS["order_items"].name
        items["_key"] = items["order_id"]
        event_frames.append(items)

    if not payments.empty:
        payments["purchase_timestamp"] = payments["order_id"].map(
            orders.set_index("order_id")["purchase_timestamp"]
        )
        payments["_event_type"] = "payment_made"
        payments["_topic"] = TOPICS["order_payments"].name
        payments["_key"] = payments["order_id"]
        event_frames.append(payments)

    if not reviews.empty:
        reviews["purchase_timestamp"] = reviews["order_id"].map(
            orders.set_index("order_id")["purchase_timestamp"]
        )
        reviews["_event_type"] = "review_submitted"
        reviews["_topic"] = TOPICS["order_reviews"].name
        reviews["_key"] = reviews["order_id"]
        event_frames.append(reviews)

    combined = pd.concat(event_frames, ignore_index=True)
    combined = combined.sort_values("purchase_timestamp").reset_index(drop=True)
    combined["purchase_timestamp"] = combined["purchase_timestamp"].astype(str)
    return combined


def row_to_payload(row: pd.Series) -> dict:
    payload = {k: v for k, v in row.items() if not k.startswith("_")}
    # convert NaT/NaN to None for JSON serialisation
    return {
        k: (None if pd.isna(v) else v)
        for k, v in payload.items()
    }


def event_stream(
    df: pd.DataFrame,
    speed_multiplier: float,
    batch_size: int,
    interval_ms: int,
) -> Iterator[list[dict]]:
    """
    Yields batches of events, sleeping between batches to simulate
    real-time flow at the configured speed multiplier.
    """
    total = len(df)
    log.info("Starting replay of %d events at %dx speed", total, speed_multiplier)

    for start in range(0, total, batch_size):
        batch = df.iloc[start : start + batch_size]
        events = []
        for _, row in batch.iterrows():
            events.append(
                {
                    "topic": row["_topic"],
                    "key": str(row["_key"]),
                    "value": row_to_payload(row),
                    "event_type": row["_event_type"],
                }
            )
        yield events

        sleep_s = (interval_ms / 1000) / speed_multiplier
        time.sleep(sleep_s)


def delivery_report(err, msg):
    if err:
        log.error("Delivery failed for %s: %s", msg.key(), err)


def run_producer(cfg: dict, dry_run: bool = False):
    dfs = load_olist(cfg)
    if not dfs:
        log.error("No data loaded — check data/olist/ directory")
        return

    events_df = build_order_events(dfs)

    replay_cfg = cfg["replay"]
    speed = float(replay_cfg["speed_multiplier"])
    batch_size = int(replay_cfg["batch_size"])
    interval_ms = int(replay_cfg["interval_ms"])

    producer = None
    if not dry_run:
        kafka_cfg = cfg["kafka"]
        prod_conf = get_producer_config(
            kafka_cfg["bootstrap_servers"],
            kafka_cfg["api_key"],
            kafka_cfg["api_secret"],
        )
        producer = Producer(prod_conf)
        log.info("Kafka producer connected to %s", kafka_cfg["bootstrap_servers"])

    total_sent = 0
    start_wall = time.time()

    for batch in event_stream(events_df, speed, batch_size, interval_ms):
        for event in batch:
            payload = json.dumps(event["value"], default=str).encode("utf-8")
            key = event["key"].encode("utf-8")

            if dry_run:
                log.debug("[DRY RUN] topic=%s key=%s", event["topic"], event["key"])
            else:
                try:
                    producer.produce(
                        topic=event["topic"],
                        key=key,
                        value=payload,
                        callback=delivery_report,
                    )
                except KafkaException as e:
                    log.error("Produce error: %s", e)

            total_sent += 1

        if producer:
            producer.poll(0)

        if total_sent % 5000 == 0:
            elapsed = time.time() - start_wall
            log.info("Progress: %d events sent | %.1fs elapsed", total_sent, elapsed)

    if producer:
        log.info("Flushing remaining messages...")
        producer.flush(timeout=30)

    elapsed = time.time() - start_wall
    log.info("Replay complete: %d events in %.1fs", total_sent, elapsed)


def main():
    parser = argparse.ArgumentParser(description="DataFlow Kafka replay producer")
    parser.add_argument("--config", default="ingestion/config.yaml")
    parser.add_argument("--speed", type=float, help="Override speed multiplier")
    parser.add_argument("--batch-size", type=int, help="Override batch size")
    parser.add_argument("--dry-run", action="store_true", help="Parse + log without sending to Kafka")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.speed:
        cfg["replay"]["speed_multiplier"] = args.speed
    if args.batch_size:
        cfg["replay"]["batch_size"] = args.batch_size

    run_producer(cfg, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
