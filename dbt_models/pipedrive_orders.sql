{% set payment_methods = ['credit_card', 'coupon', 'bank_transfer', 'gift_card'] %}

with orders as (

    select * from {{ ref('stg_orders') }}

),

payments as (

    select * from {{ ref('stg_payments') }}

),

customers as (
    select * from {{ ref('stg_customers') }}
),

order_payments as (

    select
        order_id,

        {% for payment_method in payment_methods -%}
        sum(case when payment_method = '{{ payment_method }}' then amount else 0 end) as {{ payment_method }}_amount,
        {% endfor -%}

        (sum(amount))*2 as total_amount

    from payments

    group by order_id

),

final as (

    select
        orders.order_id,
        orders.customer_id,
        orders.order_date,
        orders.status,
	case when status in ('return_pending','placed','shipped') then 'open'
	     when status in ('returned') then 'deleted'
	     when status in ('completed') then 'won' END as pipedrive_status,
	customers.last_name||' '||customers.first_name as pipedrive_title,
        order_payments.total_amount as pipedrive_value,

        {% for payment_method in payment_methods -%}

        order_payments.{{ payment_method }}_amount,

        {% endfor -%}

        order_payments.total_amount as amount

    from orders


    left join order_payments
        on orders.order_id = order_payments.order_id
    
    left join customers
        on orders.customer_id = customers.customer_id

)

select * from final
