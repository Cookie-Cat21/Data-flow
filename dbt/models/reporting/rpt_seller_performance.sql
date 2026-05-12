{{ config(materialized='table', file_format='delta') }}

-- Seller leaderboard for the live dashboard table.
-- Aggregates revenue, review scores, and SLA metrics per seller.

with seller_orders as (
    select
        i.seller_id,
        s.city                                          as seller_city,
        s.state                                         as seller_state,
        s.seller_tier,
        count(distinct i.order_id)                      as total_orders,
        sum(i.item_price)                               as total_revenue,
        sum(i.freight_value)                            as total_freight,
        count(distinct i.product_id)                    as unique_products,
        avg(r.review_score)                             as avg_review_score,
        count(case when r.sentiment = 'positive' then 1 end)    as positive_reviews,
        count(case when r.sentiment = 'negative' then 1 end)    as negative_reviews,
        sum(case when o.delivered_on_time then 1 else 0 end)::float
            / nullif(count(case when o.order_status = 'delivered' then 1 end), 0) as on_time_rate,
        avg(case when o.order_status = 'delivered'
            then o.delivery_days_actual end)            as avg_delivery_days
    from {{ ref('stg_order_items') }}   i
    left join {{ ref('dim_sellers') }}          s on i.seller_id = s.seller_id
    left join {{ ref('stg_orders') }}           o on i.order_id  = o.order_id
    left join {{ ref('stg_order_reviews') }}    r on i.order_id  = r.order_id
    group by 1, 2, 3, 4
)

select
    *,
    rank() over (order by total_revenue desc)           as revenue_rank,
    rank() over (order by avg_review_score desc nulls last) as review_rank
from seller_orders
order by total_revenue desc
