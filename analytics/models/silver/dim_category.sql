select
    category_id as id_category,
    name
from {{ source('raw', 'category') }}
