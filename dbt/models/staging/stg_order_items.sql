{{ config(materialized='view') }}

with source as (
    select * from {{ source('silver', 'order_items') }}
),

renamed as (
    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        shipping_limit_ts                       as shipping_limit_at,
        price                                   as item_price,
        freight_value,
        price + freight_value                   as item_total,
        _ingestion_date,
        _kafka_timestamp                        as ingested_at
    from source
    where order_id is not null
      and product_id is not null
)

select * from renamed
