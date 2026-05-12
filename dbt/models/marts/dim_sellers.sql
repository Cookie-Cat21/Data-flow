{{ config(materialized='table', file_format='delta') }}

with sellers as (
    select * from {{ ref('stg_sellers') }}
),

seller_stats as (
    select
        i.seller_id,
        count(distinct i.order_id)                      as total_orders,
        sum(i.item_price)                               as total_revenue,
        avg(r.review_score)                             as avg_review_score,
        sum(case when o.delivered_on_time then 1 else 0 end)::float
            / nullif(count(*), 0)                       as on_time_delivery_rate,
        count(distinct i.product_id)                    as unique_products
    from {{ ref('stg_order_items') }} i
    left join {{ ref('stg_orders') }}       o on i.order_id = o.order_id
    left join {{ ref('stg_order_reviews') }} r on i.order_id = r.order_id
    group by i.seller_id
)

select
    s.seller_id,
    s.zip_code,
    s.city,
    s.state,
    coalesce(ss.total_orders, 0)            as total_orders,
    coalesce(ss.total_revenue, 0)           as total_revenue,
    ss.avg_review_score,
    ss.on_time_delivery_rate,
    coalesce(ss.unique_products, 0)         as unique_products,
    case
        when ss.avg_review_score >= 4.5 and ss.total_orders >= 50 then 'top_seller'
        when ss.avg_review_score >= 4.0 and ss.total_orders >= 20 then 'good_seller'
        when ss.avg_review_score < 3.0  or ss.on_time_delivery_rate < 0.7 then 'at_risk'
        else 'standard'
    end                                     as seller_tier
from sellers s
left join seller_stats ss on s.seller_id = ss.seller_id
