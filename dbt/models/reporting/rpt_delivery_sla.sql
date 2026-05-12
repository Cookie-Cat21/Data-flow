{{ config(materialized='table', file_format='delta') }}

-- Delivery SLA performance by state and week.
-- Used for the delivery performance panel in the dashboard.

select
    purchase_week,
    customer_state,
    count(distinct order_id)                        as total_orders,
    count(case when order_status = 'delivered' then 1 end)  as delivered_orders,
    count(case when delivered_on_time then 1 end)   as on_time_orders,
    count(case when not delivered_on_time
                and order_status = 'delivered' then 1 end)  as late_orders,
    avg(case when order_status = 'delivered'
        then delivery_days_actual end)              as avg_delivery_days,
    avg(delivery_days_promised)                     as avg_promised_days,
    sum(case when delivered_on_time then 1 else 0 end)::float
        / nullif(count(case when order_status = 'delivered' then 1 end), 0) as sla_rate
from {{ ref('fct_orders') }}
where purchased_at is not null
group by 1, 2
order by purchase_week, customer_state
