select
    categories.id_category,
    categories.name as category_name,
    count(*) as review_count,
    (avg(reviews.sentiment_score) + 1) / 2 * 100 as satisfaction_score
from {{ ref('fact_order') }} as orders
inner join {{ ref('dim_review') }} as reviews
    on orders.id_review = reviews.id_review
inner join {{ ref('dim_category') }} as categories
    on orders.id_category = categories.id_category
where orders.id_review <> 'N/A'
group by 1, 2
order by satisfaction_score desc
