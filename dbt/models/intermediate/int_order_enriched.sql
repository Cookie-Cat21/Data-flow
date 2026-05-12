{{ config(materialized='ephemeral') }}

with orders as (
    select * from {{ ref('stg_orders') }}
),

items_agg as (
    select
        order_id,
        count(*)                        as item_count,
        sum(item_price)                 as items_subtotal,
        sum(freight_value)              as freight_total,
        sum(item_total)                 as order_subtotal,
        count(distinct seller_id)       as seller_count,
        count(distinct product_id)      as product_count
    from {{ ref('stg_order_items') }}
    group by order_id
),

payments_agg as (
    select
        order_id,
        sum(payment_value)              as payment_total,
        max(payment_installments)       as max_installments,
        -- most common payment type per order
        first(payment_type)             as primary_payment_type
    from {{ ref('stg_order_payments') }}
    group by order_id
),

reviews as (
    select
        order_id,
        review_score,
        sentiment,
        reviewed_at
    from {{ ref('stg_order_reviews') }}
    -- one review per order (take most recent if multiple)
    qualify row_number() over (partition by order_id order by reviewed_at desc) = 1
),

customers as (
    select * from {{ ref('stg_customers') }}
)

select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.city                              as customer_city,
    c.state                             as customer_state,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.shipped_at,
    o.delivered_at,
    o.estimated_delivery_at,
    o.delivery_days_actual,
    o.delivery_days_promised,
    o.delivered_on_time,

    -- items
    coalesce(i.item_count, 0)           as item_count,
    coalesce(i.seller_count, 0)         as seller_count,
    coalesce(i.items_subtotal, 0)       as items_subtotal,
    coalesce(i.freight_total, 0)        as freight_total,
    coalesce(i.order_subtotal, 0)       as order_subtotal,

    -- payment
    coalesce(p.payment_total, 0)        as payment_total,
    p.primary_payment_type,
    coalesce(p.max_installments, 1)     as max_installments,

    -- review
    r.review_score,
    r.sentiment,
    r.reviewed_at,

    -- time dimensions
    date_trunc('day', o.purchased_at)   as purchase_date,
    date_trunc('week', o.purchased_at)  as purchase_week,
    date_trunc('month', o.purchased_at) as purchase_month,
    year(o.purchased_at)                as purchase_year

from orders o
left join customers       c on o.customer_id  = c.customer_id
left join items_agg       i on o.order_id     = i.order_id
left join payments_agg    p on o.order_id     = p.order_id
left join reviews         r on o.order_id     = r.order_id
