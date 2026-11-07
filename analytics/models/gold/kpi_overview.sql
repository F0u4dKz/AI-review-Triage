select
    coalesce((select sum(line_amount) from {{ ref('fact_order') }}), 0) as sales_value,
    coalesce((select sum(quantity) from {{ ref('fact_order') }}), 0) as items_sold,
    (
        select (avg(reviews.sentiment_score) + 1) / 2 * 100
        from {{ ref('fact_order') }} as orders
        inner join {{ ref('dim_review') }} as reviews
            on orders.id_review = reviews.id_review
        where orders.id_review <> 'N/A'
    ) as satisfaction_score,
    coalesce((
        select count(*)
        from {{ ref('fact_order') }}
        where id_review <> 'N/A'
    ), 0) as review_count
