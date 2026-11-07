with latest_review as (
    select
        order_id,
        product_id,
        review_id
    from {{ source('raw', 'reviews_enrichment') }}
    qualify row_number() over (
        partition by order_id, product_id
        order by processed_at desc
    ) = 1
)

select
    items.order_id as id_order,
    items.product_id as id_product,
    orders.client_id as id_client,
    payments.payment_id as id_payment,
    products.category_id as id_category,
    coalesce(latest_review.review_id, 'N/A') as id_review,
    items.quantity,
    items.unit_price,
    items.quantity * items.unit_price as line_amount,
    orders.order_date,
    orders.status as order_status
from {{ source('raw', 'order_items') }} as items
inner join {{ source('raw', 'order_head') }} as orders
    on items.order_id = orders.order_id
inner join {{ source('raw', 'product') }} as products
    on items.product_id = products.product_id
inner join {{ source('raw', 'payments') }} as payments
    on items.order_id = payments.order_id
left join latest_review
    on items.order_id = latest_review.order_id
    and items.product_id = latest_review.product_id
where orders.status = 'delivered'
