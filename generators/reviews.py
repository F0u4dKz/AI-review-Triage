"""Stream mock reviews to the FastAPI webhook, one every N seconds.

Reviews use real IDs from landing/transactions/*.parquet. The intended labels
are written to data/mock/reviews_ground_truth.jsonl (never sent to the API).
"""

import argparse
import json
import random
import time
import uuid
from datetime import datetime, timedelta

import duckdb
import httpx
from faker import Faker

from generators import config as cfg
from generators.review_templates import (
    ISSUE_CATEGORIES,
    PII_SUFFIXES,
    RATING_RANGE,
    SENTIMENTS,
    TEMPLATES,
)

CANDIDATES_SQL = """
SELECT
    oi.order_id,
    oh.client_id,
    oi.product_id,
    p.name AS product_name,
    oh.status AS order_status,
    d.carrier,
    d.delivered_at,
    d.is_late,
    date_diff('day', d.promised_date, d.delivered_at::DATE) AS days_late,
    pay.status AS payment_status
FROM read_parquet('{d}/order_items.parquet') oi
JOIN read_parquet('{d}/order_head.parquet') oh USING (order_id)
JOIN read_parquet('{d}/product.parquet') p USING (product_id)
JOIN read_parquet('{d}/deliveries.parquet') d USING (order_id)
JOIN read_parquet('{d}/payments.parquet') pay USING (order_id)
WHERE oh.status IN ('delivered', 'returned') AND d.delivered_at IS NOT NULL
"""


def load_candidates() -> list[dict]:
    if not (cfg.TRANSACTIONS_DIR / "order_items.parquet").exists():
        raise SystemExit("No transactional data found. Run `make mock-transactions` first.")
    rel = duckdb.sql(CANDIDATES_SQL.format(d=cfg.TRANSACTIONS_DIR.as_posix()))
    return [dict(zip(rel.columns, row)) for row in rel.fetchall()]


def pick_labels(item: dict, rng: random.Random) -> tuple[str, str]:
    """Choose the intended (category, sentiment), biased by what happened to the order."""
    if item["is_late"] and rng.random() < 0.75:
        return "delivery", "negative"
    if item["payment_status"] != "paid" and rng.random() < 0.6:
        return "payment", rng.choices(["negative", "neutral"], weights=[80, 20])[0]
    if item["order_status"] == "returned" and rng.random() < 0.6:
        return "quality", "negative"
    category = rng.choices(ISSUE_CATEGORIES, weights=[20, 25, 15, 15, 10, 15])[0]
    sentiment = rng.choices(SENTIMENTS, weights=[55, 20, 25])[0]
    return category, sentiment


def pick_rating(sentiment: str, mismatch: bool, rng: random.Random) -> int:
    if mismatch:
        sentiment = {"positive": "negative", "negative": "positive", "neutral": rng.choice(["positive", "negative"])}[sentiment]
    low, high = RATING_RANGE[sentiment]
    return rng.randint(low, high)


def build_review(item: dict, rng: random.Random, fake: Faker) -> tuple[dict, dict]:
    category, sentiment = pick_labels(item, rng)
    days_late = max(item["days_late"] or 0, 1)
    text = rng.choice(TEMPLATES[category][sentiment]).format(
        product=item["product_name"],
        carrier=item["carrier"],
        days_late=f"{days_late} day" if days_late == 1 else f"{days_late} days",
    )

    has_pii = rng.random() < cfg.PII_RATE
    if has_pii:
        text += rng.choice(PII_SUFFIXES).format(email=fake.email(), phone=fake.phone_number())

    mismatch = rng.random() < cfg.MISMATCH_RATE
    created_at = min(
        item["delivered_at"] + timedelta(days=rng.randint(0, 10), hours=rng.randint(0, 23)),
        datetime.now(),
    )

    payload = {
        "review_id": str(uuid.UUID(int=rng.getrandbits(128), version=4)),
        "source": rng.choice(cfg.REVIEW_SOURCES),
        "order_id": item["order_id"],
        "client_id": item["client_id"],
        "product_id": item["product_id"],
        "rating": pick_rating(sentiment, mismatch, rng),
        "text": text,
        "created_at": created_at.isoformat(timespec="seconds"),
    }
    truth = {
        "review_id": payload["review_id"],
        "category": category,
        "sentiment": sentiment,
        "rating_mismatch": mismatch,
        "has_pii": has_pii,
    }
    return payload, truth


def send(client: httpx.Client | None, url: str, payload: dict) -> str:
    if client is None:
        return "dry-run"
    try:
        response = client.post(url, json=payload)
        return str(response.status_code)
    except httpx.HTTPError as exc:
        return f"error: {type(exc).__name__}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=cfg.STREAM_INTERVAL_SECONDS, help="seconds between reviews")
    parser.add_argument("--url", default=cfg.API_URL)
    parser.add_argument("--api-key", default=cfg.API_KEY)
    parser.add_argument("--count", type=int, default=0, help="stop after N reviews (0 = run forever)")
    parser.add_argument("--seed", type=int, default=None, help="fix the random seed")
    parser.add_argument("--dry-run", action="store_true", help="print payloads instead of sending them")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    fake = Faker(cfg.FAKER_LOCALE)
    fake.seed_instance(args.seed)
    candidates = load_candidates()
    sent: list[dict] = []

    client = None if args.dry_run else httpx.Client(headers={"X-API-Key": args.api_key}, timeout=5.0)
    if not args.dry_run:
        cfg.GROUND_TRUTH_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Streaming reviews from {len(candidates)} delivered order items -> {'stdout' if args.dry_run else args.url}")
    n = 0
    try:
        while args.count == 0 or n < args.count:
            if sent and rng.random() < cfg.DUPLICATE_RATE:
                payload, label = rng.choice(sent), "duplicate"
            else:
                payload, truth = build_review(rng.choice(candidates), rng, fake)
                sent.append(payload)
                label = f"{truth['category']}/{truth['sentiment']}"
                if not args.dry_run:
                    with cfg.GROUND_TRUTH_PATH.open("a") as f:
                        f.write(json.dumps(truth) + "\n")

            status = send(client, args.url, payload)
            n += 1
            if args.dry_run:
                print(json.dumps(payload, ensure_ascii=False))
            print(f"[{n}] {status:<22} {label:<20} rating={payload['rating']} order={payload['order_id']}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nStopped after {n} reviews.")
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
