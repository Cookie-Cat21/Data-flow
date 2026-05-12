# ADR 003 — dbt Core over raw SQL scripts for the Gold transformation layer

**Status:** Accepted

## Context

Silver → Gold transformations can be written as raw SQL scripts run by
Spark or executed directly against Databricks SQL. dbt adds a dependency
and a new tool to learn.

## Decision

Use dbt Core (with the `dbt-databricks` adapter) for all Silver → Gold
transformations, integrated into Airflow via Astronomer Cosmos.

## Rationale

**Lineage is automatic.** dbt builds a DAG of models based on `{{ ref() }}`
calls. Every model knows what it depends on. Astronomer Cosmos converts this
DAG into Airflow tasks — you get per-model retries and the full Airflow UI
for free.

**Tests are first-class.** `schema.yml` tests (not_null, unique,
accepted_values, relationships) run after each model. A broken upstream
Silver table fails loudly at the dbt test step, not silently in a
downstream BI dashboard.

**Documentation generates itself.** `dbt docs generate` produces a
searchable data dictionary with lineage graphs, column descriptions, and
test results. This is a portfolio artifact in itself.

**SQL is the right abstraction for analytical transforms.** Business logic
like "a champion customer has ≥5 orders" belongs in SQL `CASE` statements,
not in PySpark. dbt keeps this readable and reviewable.

**vs. raw SQL scripts:**

| Concern | Raw SQL | dbt |
|---|---|---|
| Dependency management | Manual (run order matters) | Automatic via `{{ ref() }}` |
| Testing | Write your own | Built-in schema tests |
| Documentation | Write your own | Auto-generated from schema.yml |
| Idempotency | Must handle manually | `--full-refresh` flag |
| Incremental loads | Must implement yourself | `incremental` materialization |

## Trade-offs

- **Learning curve:** dbt Jinja syntax and materialization strategies are
  non-trivial. Worth it — dbt is a top-10 skill in analytics engineering JDs.
- **Debugging:** Compiled SQL lives in `target/` and is inspectable.
  Model errors surface clearly in the Airflow task logs.

## Consequence

All Gold models live under `dbt/models/`. The Cosmos DAG in Airflow runs
`dbt build` which executes models + tests in dependency order. dbt docs
are published as a static site alongside the dashboard.
