with ranked as (
    select
        *,
        row_number() over (partition by review_id order by processed_at desc) as row_number
    from {{ source('raw', 'reviews_enrichment') }}
)

select
    review_id as id_review,
    rating,
    sentiment_score,
    sentiment_label,
    category as issue_category,
    is_urgent
from ranked
where row_number = 1

union all

select
    'N/A' as id_review,
    null as rating,
    null as sentiment_score,
    null as sentiment_label,
    null as issue_category,
    null as is_urgent
