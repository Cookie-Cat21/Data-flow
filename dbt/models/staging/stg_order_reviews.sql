{{ config(materialized='view') }}

with source as (
    select * from {{ source('silver', 'order_reviews') }}
),

renamed as (
    select
        review_id,
        order_id,
        review_score,
        review_comment_title,
        review_comment_message,
        review_creation_ts                          as reviewed_at,
        review_answer_timestamp                     as answered_at,
        case
            when review_score >= 4 then 'positive'
            when review_score = 3  then 'neutral'
            else 'negative'
        end                                         as sentiment,
        _ingestion_date,
        _kafka_timestamp                            as ingested_at
    from source
    where order_id is not null
      and review_score between 1 and 5
)

select * from renamed
