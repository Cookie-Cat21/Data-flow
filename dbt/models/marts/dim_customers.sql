{{ config(materialized='table', file_format='delta') }}

with customers as (
    select * from {{ ref('stg_customers') }}
),

order_stats as (
    select
        customer_unique_id,
        count(distinct order_id)                        as lifetime_orders,
        sum(payment_total)                              as lifetime_value,
        min(purchased_at)                               as first_order_at,
        max(purchased_at)                               as last_order_at,
        avg(review_score)                               as avg_review_score
    from {{ ref('int_order_enriched') }}
    group by customer_unique_id
)

select
    c.customer_id,
    c.customer_unique_id,
    c.zip_code,
    c.city,
    c.state,
    coalesce(s.lifetime_orders, 0)      as lifetime_orders,
    coalesce(s.lifetime_value, 0)       as lifetime_value,
    s.first_order_at,
    s.last_order_at,
    s.avg_review_score,
    case
        when s.lifetime_orders >= 5  then 'champion'
        when s.lifetime_orders >= 3  then 'loyal'
        when s.lifetime_orders >= 2  then 'returning'
        else 'new'
    end                                 as customer_segment
from customers c
left join order_stats s on c.customer_unique_id = s.customer_unique_id
