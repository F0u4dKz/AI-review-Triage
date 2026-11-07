select
    payment_id as id_payment,
    order_id as id_order,
    method,
    status,
    amount,
    paid_at
from {{ source('raw', 'payments') }}
