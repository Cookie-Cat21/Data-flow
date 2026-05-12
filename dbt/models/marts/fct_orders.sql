{{ config(materialized='table', file_format='delta') }}

select * from {{ ref('int_order_enriched') }}
