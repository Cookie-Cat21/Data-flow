# ADR 001 — Kafka over direct database writes for event ingestion

**Status:** Accepted

## Context

The Olist CSV replay producer needs to deliver order events to downstream
consumers (Spark streaming, potential future consumers). The simplest
implementation would write events directly to a database table.

## Decision

Use Apache Kafka (Confluent Cloud) as the event bus rather than writing
directly to a database.

## Rationale

| Concern | Direct DB write | Kafka |
|---|---|---|
| Consumer decoupling | Tight — consumers query the DB | Loose — consumers subscribe independently |
| Replay / reprocessing | Requires table scans + deletes | Consumers reset offset to any point |
| Schema evolution | ALTER TABLE risks | Schema Registry handles it cleanly |
| Multiple consumers | N readers hit the DB simultaneously | Each consumer group reads independently |
| Backpressure | Producer blocked if DB is slow | Kafka absorbs bursts, Spark reads at its pace |

In production at scale, a direct DB write becomes a bottleneck as soon as
you have >1 downstream consumer. Kafka's log-based architecture means the
Spark streaming job, a potential BI tool, and a future alerting system can
all consume the same events without coupling.

## Trade-offs

- **Added complexity:** Confluent Cloud account + Kafka SDK dependency.
- **Latency:** Negligible for this use case (~5ms vs. sub-ms for local DB).
- **Cost:** Free tier covers this project; would cost ~$50/month at moderate
  production load.

## Consequence

The producer publishes to topic-per-entity (orders, payments, reviews).
The Spark bronze_writer reads all topics in a single streaming job using
Kafka's `subscribe` pattern. New consumers can be added without touching
the producer.
