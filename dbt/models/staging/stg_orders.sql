{{ config(materialized='view') }}

with source as (
    select * from {{ source('silver', 'orders') }}
),

renamed as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_ts                               as purchased_at,
        order_approved_ts                               as approved_at,
        order_delivered_carrier_ts                      as shipped_at,
        order_delivered_customer_ts                     as delivered_at,
        order_estimated_delivery_ts                     as estimated_delivery_at,

        -- derived fields
        datediff(order_delivered_customer_ts, order_purchase_ts)    as delivery_days_actual,
        datediff(order_estimated_delivery_ts, order_purchase_ts)    as delivery_days_promised,
        case
            when order_delivered_customer_ts <= order_estimated_delivery_ts then true
            else false
        end                                             as delivered_on_time,

        _ingestion_date,
        _kafka_timestamp                                as ingested_at

    from source
    where order_id is not null
      and order_purchase_ts is not null
)

select * from renamed
