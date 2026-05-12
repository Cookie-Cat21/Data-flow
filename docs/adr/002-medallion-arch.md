# ADR 002 — Medallion architecture (Bronze / Silver / Gold) over a flat schema

**Status:** Accepted

## Context

Raw Olist data needs to be stored and transformed for analytics. The
simplest approach would be to clean the data once and store it in a
single "clean" layer.

## Decision

Implement a three-layer medallion architecture using Delta Lake:

- **Bronze** — raw Kafka payloads, exactly as received, with Kafka metadata
- **Silver** — typed, deduplicated, null-filtered; one row per natural key
- **Gold** — business-ready aggregates and dimensional models built by dbt

## Rationale

**Why not a single clean layer?**

A flat schema collapses ingestion concerns and business logic into one
place. When a business rule changes (e.g., how "on-time" is defined), you
must re-ingest from source. With medallion, you re-run only the Gold layer.

**Why Bronze needs to be raw:**

Bronze is an insurance policy. If Silver cleaning has a bug, Bronze lets
you replay the correct transformation without re-ingesting from Kafka.
Delta Lake time travel means you can inspect the state of Bronze at any
point in history — essential for debugging late-arriving data.

**Why Silver is batch, not streaming:**

Silver applies deduplication (windowed `dropDuplicates` in Spark Structured
Streaming is expensive for large windows). Running Silver as a scheduled
batch job is simpler, cheaper, and correct for our 6-hour pipeline cadence.

**Why Gold is dbt:**

dbt enforces SQL-as-code with full lineage, testing, and documentation.
The Gold layer models are business logic — they should be version-controlled,
tested, and reviewable as SQL, not buried in a Spark notebook.

## Trade-offs

- **Storage cost:** Three copies of the data. At Olist scale (~GB), negligible.
  At TB scale, Bronze should have a shorter retention window.
- **Pipeline latency:** Bronze → Silver → Gold adds 2–3 pipeline stages.
  For near-real-time use cases (<1 min), consider a streaming Silver layer.

## Consequence

The `dbt_project.yml` sources point to Silver tables. Gold models are
materialized as Delta tables. Airflow runs Silver → dbt in sequence.
