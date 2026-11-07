select
    client_id as id_client,
    name,
    city,
    signup_date
from {{ source('raw', 'clients') }}
