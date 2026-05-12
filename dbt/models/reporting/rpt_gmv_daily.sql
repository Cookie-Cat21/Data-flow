{{ config(materialized='table', file_format='delta') }}

-- Daily GMV, order count, and average order value.
-- Primary feed for the live dashboard GMV time-series chart.

select
    purchase_date,
    purchase_year,
    date_trunc('month', purchase_date)          as purchase_month,
    count(distinct order_id)                    as order_count,
    count(distinct customer_unique_id)          as unique_customers,
    sum(payment_total)                          as gmv,
    avg(payment_total)                          as avg_order_value,
    sum(freight_total)                          as total_freight,
    sum(payment_total) - sum(freight_total)     as net_gmv,
    sum(case when order_status = 'delivered' then payment_total else 0 end) as delivered_gmv,
    sum(case when delivered_on_time then 1 else 0 end)::float
        / nullif(count(case when order_status = 'delivered' then 1 end), 0) as on_time_rate
from {{ ref('fct_orders') }}
group by 1, 2, 3
order by purchase_date
