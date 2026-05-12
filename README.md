# DataFlow

A production-grade real-time e-commerce analytics pipeline demonstrating the modern data engineering stack: **Kafka → Spark Structured Streaming → Delta Lake (medallion) → dbt → Airflow → Next.js live dashboard**.

> **Dataset:** [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — 100K+ real orders, 9 relational tables, CC BY-NC-SA 4.0.

---

## Architecture

```
CSV Replay Producer
      │
      ▼  (Confluent Cloud)
  Apache Kafka  ──────────────────────────────────────────────────────┐
      │                                                                │
      ▼  (Spark Structured Streaming)                                 │
  Bronze Delta  (raw events + Kafka metadata)                         │
      │                                                                │
      ▼  (Spark batch job)                                            │
  Silver Delta  (typed, deduplicated, cleaned)                        │
      │                                                                │
      ▼  (dbt Core + Astronomer Cosmos)                               │
  Gold Delta    (fct_orders, dim_*, rpt_*)                            │
      │                                                                │
      ▼  (PostgreSQL mirror + Node.js WS server)                      │
  Next.js Dashboard  ◄───────────────────────────────────────────────┘
                          WebSocket (live updates every 5s)
```

Orchestrated end-to-end by **Apache Airflow** (Astro CLI).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Event streaming | Apache Kafka (Confluent Cloud) |
| Stream processing | Apache Spark Structured Streaming (Databricks) |
| Storage | Delta Lake (Bronze / Silver / Gold) |
| Transformation | dbt Core + dbt-databricks adapter |
| Orchestration | Apache Airflow + Astronomer Cosmos |
| Dashboard | Next.js 14, Recharts, WebSocket |
| Data quality | Great Expectations (Silver layer) |

---

## Repo Structure

```
dataflow/
├── ingestion/          # Kafka producer + topic config
│   ├── producer.py
│   ├── topics.py
│   └── config.yaml
├── spark/              # Spark jobs
│   ├── schemas.py
│   ├── bronze_writer.py
│   └── silver_cleaner.py
├── dbt/                # dbt project
│   ├── models/
│   │   ├── staging/    # stg_* views (Silver source)
│   │   ├── intermediate/  # int_* ephemeral joins
│   │   ├── marts/      # fct_orders, dim_*
│   │   └── reporting/  # rpt_gmv_daily, rpt_delivery_sla, rpt_seller_performance
│   └── dbt_project.yml
├── airflow/
│   └── dags/
│       ├── pipeline_dag.py   # Main orchestration DAG
│       └── dbt_dag.py        # Cosmos dbt DAG
├── dashboard/          # Next.js live dashboard
│   ├── app/
│   ├── components/
│   ├── server/ws-server.ts
│   └── package.json
├── docs/
│   └── adr/            # Architecture Decision Records
├── data/olist/         # Raw CSVs (gitignored — download from Kaggle)
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Get the data

Download the [Olist dataset from Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and extract all CSVs into `data/olist/`.

### 2. Configure environment

```bash
cp .env.example .env
# Fill in: KAFKA_BOOTSTRAP_SERVERS, KAFKA_API_KEY, KAFKA_API_SECRET,
#           DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
```

### 3. Install Python dependencies

```bash
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 4. Test the producer (dry run — no Kafka needed)

```bash
python -m ingestion.producer --dry-run --speed 1000
```

### 5. Run the Kafka producer (requires Confluent Cloud)

```bash
python -m ingestion.producer --speed 100
```

### 6. Start the Spark Bronze writer (on Databricks)

Upload `spark/bronze_writer.py` to DBFS and run as a Databricks job, or submit locally:

```bash
spark-submit spark/bronze_writer.py
```

### 7. Run Silver cleaner

```bash
spark-submit spark/silver_cleaner.py
```

### 8. Run dbt

```bash
cd dbt
dbt deps
dbt build --target dev
dbt docs generate && dbt docs serve   # optional: browse lineage
```

### 9. Start Airflow (Astro CLI)

```bash
astro dev start
# Open http://localhost:8080 → trigger "dataflow_pipeline" DAG
```

### 10. Start the dashboard

```bash
cd dashboard
npm install
npm run ws-server &   # WebSocket server (port 8080)
npm run dev           # Next.js (port 3000)
# Open http://localhost:3000
```

---

## dbt Model Lineage

```
stg_orders ──┐
stg_items ───┤
stg_payments─┤──► int_order_enriched ──► fct_orders ──► rpt_gmv_daily
stg_reviews ─┤                       └──► rpt_delivery_sla
stg_customers┘                       └──► rpt_seller_performance

stg_customers ──► dim_customers
stg_sellers ────► dim_sellers
stg_products ───► dim_products
```

---

## Architecture Decision Records

- [ADR 001 — Kafka over direct DB writes](docs/adr/001-kafka-over-direct.md)
- [ADR 002 — Medallion architecture](docs/adr/002-medallion-arch.md)
- [ADR 003 — dbt over raw SQL scripts](docs/adr/003-dbt-over-sql.md)

---

## Key design choices

**Why PERMISSIVE mode in Bronze?** Bad records go to a `_corrupt_record` column instead of failing the stream. A dead-letter Kafka topic captures them for inspection without blocking the pipeline.

**Why ephemeral for `int_order_enriched`?** The intermediate model is a complex join used by multiple Gold models. `ephemeral` means it compiles inline — no extra table materialization, no extra storage.

**Why Astronomer Cosmos for dbt in Airflow?** Cosmos turns each dbt model into a native Airflow task. You get per-model retries, dependency visualisation in the Airflow graph view, and dbt test tasks auto-wired after each model — all without writing any Airflow task code.
