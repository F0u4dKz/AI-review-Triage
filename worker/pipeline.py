"""Move a review inbox -> processing -> done, or to failed after 3 bad tries.

A rename from inbox to processing claims the file. Leftover files in processing
are picked up again on the next pass. Enrichments are written as one parquet
per batch, then the claimed JSON files move to done.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

from api.schemas.review import ReviewIn
from api.services.inbox import LANDING_STATES
from worker.classify import classify
from worker.config import WorkerSettings
from worker.pii import redact
from worker.schemas import Enrichment
from worker.urgency import is_urgent


def ensure_dirs(landing: Path) -> None:
    for name in (*LANDING_STATES, "enrichments"):
        (landing / name).mkdir(parents=True, exist_ok=True)


def claim_inbox(landing: Path) -> list[Path]:
    processing = landing / "processing"
    claimed: list[Path] = []
    for src in sorted((landing / "inbox").glob("*.json")):
        dest = processing / src.name
        if dest.exists():
            continue
        try:
            os.rename(src, dest)
        except FileNotFoundError:
            continue
        claimed.append(dest)
    return claimed


def waiting_files(landing: Path) -> list[Path]:
    already = sorted((landing / "processing").glob("*.json"))
    return already + claim_inbox(landing)


def register_failure(path: Path, exc: Exception, settings: WorkerSettings) -> None:
    tries_path = path.with_suffix(".tries")
    try:
        tries = int(tries_path.read_text(encoding="utf-8")) + 1
    except (OSError, ValueError):
        tries = 1

    message = f"{type(exc).__name__}: {exc}"[:2000]
    if tries >= settings.max_tries:
        failed = settings.landing_dir / "failed"
        os.rename(path, failed / path.name)
        (failed / f"{path.stem}.error.txt").write_text(message, encoding="utf-8")
        tries_path.unlink(missing_ok=True)
        print(f"{path.stem} moved to failed after {tries} tries")
        return

    tries_path.write_text(str(tries), encoding="utf-8")
    print(f"{path.stem} try {tries}/{settings.max_tries} failed: {message[:200]}")


def enrich_file(path: Path, settings: WorkerSettings, client: httpx.Client) -> Enrichment:
    review = ReviewIn.model_validate_json(path.read_text(encoding="utf-8"))
    redacted = redact(review.text)
    labeled = classify(redacted, review.rating, settings, client)
    return Enrichment(
        review_id=review.review_id,
        order_id=review.order_id,
        client_id=review.client_id,
        product_id=review.product_id,
        rating=review.rating,
        redacted_text=redacted,
        category=labeled.category,
        sentiment_score=labeled.sentiment_score,
        sentiment_label=labeled.sentiment_label,
        key_issues=[item.strip() for item in labeled.key_issues if item.strip()],
        is_urgent=is_urgent(review.rating, labeled.sentiment_score, review.text),
        model_name=settings.model_name,
        processed_at=datetime.now(timezone.utc),
    )


def flush(pending: list[tuple[Path, Enrichment]], landing: Path) -> None:
    if not pending:
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = landing / "enrichments" / f"{stamp}.parquet"
    rows = [row.model_dump() for _, row in pending]
    pd.DataFrame(rows).to_parquet(target, index=False)
    done = landing / "done"
    for path, _ in pending:
        os.rename(path, done / path.name)
        path.with_suffix(".tries").unlink(missing_ok=True)
    print(f"flushed {len(pending)} reviews -> {target.name}")


def run_once(settings: WorkerSettings, client: httpx.Client) -> int:
    ensure_dirs(settings.landing_dir)
    pending: list[tuple[Path, Enrichment]] = []
    written = 0
    for path in waiting_files(settings.landing_dir):
        try:
            row = enrich_file(path, settings, client)
        except Exception as exc:
            register_failure(path, exc, settings)
            continue
        print(f"{row.review_id} {row.category} {row.sentiment_label} urgent={row.is_urgent}")
        pending.append((path, row))
        if len(pending) >= settings.batch_size:
            flush(pending, settings.landing_dir)
            written += len(pending)
            pending = []
    flush(pending, settings.landing_dir)
    written += len(pending)
    return written
