select
    product_id as id_product,
    category_id as id_category,
    name,
    price
from {{ source('raw', 'product') }}
