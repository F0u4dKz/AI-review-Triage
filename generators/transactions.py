"""Generate linked e-commerce tables and write them to landing/transactions/*.parquet."""

import random
from datetime import date, datetime, time, timedelta

import pandas as pd
from faker import Faker

from generators import config as cfg


def build_tables(seed: int = cfg.SEED, today: date | None = None) -> dict[str, pd.DataFrame]:
    rng = random.Random(seed)
    Faker.seed(seed)
    fake = Faker(cfg.FAKER_LOCALE)
    now = datetime.combine(today or date.today(), time(0, 0))

    categories = pd.DataFrame({
        "category_id": range(1, len(cfg.CATEGORIES) + 1),
        "name": cfg.CATEGORIES,
    })

    products = pd.DataFrame(cfg.PRODUCTS, columns=["product_id", "category_id", "name", "price"])
    price_of = dict(zip(products.product_id, products.price))

    clients = pd.DataFrame([{
        "client_id": i,
        "name": fake.name(),
        "email": fake.email(),
        "city": fake.city(),
        "signup_date": (now - timedelta(days=rng.randint(30, 365))).date(),
    } for i in range(1, cfg.N_CLIENTS + 1)])
    signup_of = dict(zip(clients.client_id, clients.signup_date))

    window_start = now - timedelta(days=cfg.ORDER_WINDOW_DAYS)
    window_end = now - timedelta(days=1)
    orders = []
    for order_id in range(1, cfg.N_ORDERS + 1):
        client_id = rng.randint(1, cfg.N_CLIENTS)
        start = max(window_start, datetime.combine(signup_of[client_id], time(0, 0)))
        seconds = int((window_end - start).total_seconds())
        orders.append({
            "order_id": order_id,
            "client_id": client_id,
            "order_date": start + timedelta(seconds=rng.randint(0, seconds)),
            "status": rng.choices(["delivered", "cancelled", "returned"], weights=[86, 7, 7])[0],
        })
    order_head = pd.DataFrame(orders)

    items, item_id = [], 1
    for order_id in order_head.order_id:
        for product_id in rng.sample(list(price_of), k=rng.randint(1, 3)):
            items.append({
                "order_item_id": item_id,
                "order_id": order_id,
                "product_id": product_id,
                "quantity": rng.randint(1, 3),
                "unit_price": price_of[product_id],
            })
            item_id += 1
    order_items = pd.DataFrame(items)

    line_totals = (order_items.quantity * order_items.unit_price).groupby(order_items.order_id).sum()
    order_head["total_amount"] = order_head.order_id.map(line_totals).round(2)

    deliveries = []
    for order in order_head[order_head.status != "cancelled"].itertuples():
        shipped_at = order.order_date + timedelta(days=rng.randint(0, 2), hours=rng.randint(1, 10))
        promised_date = (shipped_at + timedelta(days=3)).date()
        is_late = rng.random() < cfg.LATE_DELIVERY_RATE
        if is_late:
            delivered_at = datetime.combine(promised_date, time(rng.randint(8, 19))) + timedelta(days=rng.randint(1, 7))
        else:
            delivered_at = shipped_at + timedelta(days=rng.randint(1, 3), hours=rng.randint(0, 6))

        if shipped_at >= now:
            shipped_at, delivered_at = None, None
            order_head.loc[order_head.order_id == order.order_id, "status"] = "processing"
        elif delivered_at >= now:
            delivered_at = None
            order_head.loc[order_head.order_id == order.order_id, "status"] = "shipped"

        deliveries.append({
            "delivery_id": order.order_id,
            "order_id": order.order_id,
            "carrier": rng.choice(cfg.CARRIERS),
            "shipped_at": shipped_at,
            "promised_date": promised_date,
            "delivered_at": delivered_at,
            "is_late": is_late,
        })
    deliveries = pd.DataFrame(deliveries)

    payments = []
    for order in order_head.itertuples():
        if order.status in ("cancelled", "returned"):
            status = "refunded"
        else:
            status = rng.choices(["paid", "failed_then_paid", "refunded"], weights=[88, 7, 5])[0]
        payments.append({
            "payment_id": order.order_id,
            "order_id": order.order_id,
            "amount": order.total_amount,
            "method": rng.choice(cfg.PAYMENT_METHODS),
            "status": status,
            "paid_at": order.order_date + timedelta(minutes=rng.randint(1, 30)),
        })
    payments = pd.DataFrame(payments)

    return {
        "category": categories,
        "product": products,
        "clients": clients,
        "order_head": order_head,
        "order_items": order_items,
        "deliveries": deliveries,
        "payments": payments,
    }


def main() -> None:
    cfg.TRANSACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in build_tables().items():
        df.to_parquet(cfg.TRANSACTIONS_DIR / f"{name}.parquet", index=False)
        print(f"{name:<12} {len(df):>4} rows")


if __name__ == "__main__":
    main()
