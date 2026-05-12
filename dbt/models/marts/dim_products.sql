{{ config(materialized='table', file_format='delta') }}

with products as (
    select * from {{ ref('stg_products') }}
),

-- Olist provides an English translation table
category_translation as (
    select
        product_category_name,
        product_category_name_english
    from {{ source('silver', 'product_category_name_translation') }}
),

product_sales as (
    select
        product_id,
        count(distinct order_id)            as total_orders,
        sum(item_price)                     as total_revenue,
        avg(item_price)                     as avg_price,
        sum(freight_value)                  as total_freight
    from {{ ref('stg_order_items') }}
    group by product_id
)

select
    p.product_id,
    p.category_name_pt,
    coalesce(t.product_category_name_english, p.category_name_pt) as category_name_en,
    p.photo_count,
    p.weight_g,
    p.volume_cm3,
    coalesce(ps.total_orders, 0)            as total_orders,
    coalesce(ps.total_revenue, 0)           as total_revenue,
    ps.avg_price,
    coalesce(ps.total_freight, 0)           as total_freight
from products p
left join category_translation  t  on p.category_name_pt = t.product_category_name
left join product_sales         ps on p.product_id        = ps.product_id
