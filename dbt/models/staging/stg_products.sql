{{ config(materialized='view') }}

with source as (
    select * from {{ source('silver', 'products') }}
),

renamed as (
    select
        product_id,
        product_category_name                   as category_name_pt,
        product_name_length,
        product_description_length,
        product_photos_qty                      as photo_count,
        product_weight_g                        as weight_g,
        product_length_cm                       as length_cm,
        product_height_cm                       as height_cm,
        product_width_cm                        as width_cm,
        (product_length_cm * product_height_cm * product_width_cm) as volume_cm3
    from source
    where product_id is not null
)

select * from renamed
