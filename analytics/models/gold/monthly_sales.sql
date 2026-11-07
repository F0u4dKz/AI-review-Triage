select
    date_trunc('month', order_date) as sales_month,
    sum(line_amount) as sales_value,
    sum(quantity) as items_sold
from {{ ref('fact_order') }}
group by 1
order by 1
