import json
from pathlib import Path

import httpx
import pandas as pd
import pytest
from faker import Faker

from worker.config import WorkerSettings
from worker.pii import redact
from worker.pipeline import run_once
from worker.urgency import is_urgent

GOOD = {
    "category": "price",
    "sentiment_score": -0.8,
    "sentiment_label": "negative",
    "key_issues": ["overpriced"],
}


def review(review_id: str = "abc123", **overrides: object) -> dict:
    body = {
        "review_id": review_id,
        "source": "form",
        "order_id": 17,
        "client_id": 18,
        "product_id": 3,
        "rating": 2,
        "text": "Way too expensive for what the Coffee Maker is.",
        "created_at": "2026-08-23T07:13:50",
    }
    body.update(overrides)
    return body


def write_inbox(landing: Path, body: dict) -> None:
    inbox = landing / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    (inbox / f"{body['review_id']}.json").write_text(json.dumps(body), encoding="utf-8")


def client_returning(payload: dict, capture: list[dict] | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"role": "assistant", "content": json.dumps(payload)}})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_redacts_french_email_and_phone() -> None:
    fake = Faker("fr_FR")
    fake.seed_instance(42)
    for _ in range(25):
        email = fake.email()
        phone = fake.phone_number()
        redacted = redact(f"You can reach me at {email}. Call me back on {phone} please.")
        assert email not in redacted
        assert phone not in redacted
        assert "[EMAIL]" in redacted
        assert "[PHONE]" in redacted


@pytest.mark.parametrize(
    ("rating", "score", "text", "expected"),
    [
        (2, -0.6, "Too expensive.", True),
        (2, -0.5, "Too expensive.", False),
        (3, -0.9, "Too expensive.", False),
        (5, 0.2, "I want a refund now.", True),
        (5, 0.2, "Never again.", True),
    ],
)
def test_urgency_rule(rating: int, score: float, text: str, expected: bool) -> None:
    assert is_urgent(rating, score, text) is expected


def test_run_once_labels_and_flushes(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    write_inbox(
        landing,
        review(text="Way too expensive. You can reach me at ada@example.com or 06 12 34 56 78."),
    )
    capture: list[dict] = []
    settings = WorkerSettings(landing_dir=landing, model_name="llama3")

    written = run_once(settings, client_returning(GOOD, capture))

    assert written == 1
    assert not (landing / "inbox" / "abc123.json").exists()
    assert not (landing / "processing" / "abc123.json").exists()
    saved = json.loads((landing / "done" / "abc123.json").read_text(encoding="utf-8"))
    assert saved["text"].startswith("Way too expensive.")

    frame = pd.read_parquet(next((landing / "enrichments").glob("*.parquet")))
    row = frame.iloc[0]
    assert row["review_id"] == "abc123"
    assert row["order_id"] == 17
    assert row["client_id"] == 18
    assert row["product_id"] == 3
    assert row["rating"] == 2
    assert row["category"] == "price"
    assert row["sentiment_score"] == -0.8
    assert row["is_urgent"]
    assert "[EMAIL]" in row["redacted_text"]
    assert "[PHONE]" in row["redacted_text"]
    assert "ada@example.com" not in row["redacted_text"]

    sent = capture[0]
    assert sent["model"] == "llama3"
    assert sent["stream"] is False
    assert sent["options"]["temperature"] == 0
    assert "ada@example.com" not in sent["messages"][0]["content"]
    assert "[EMAIL]" in sent["messages"][0]["content"]
    assert sent["format"]["properties"]["sentiment_score"]["minimum"] == -1


def test_rejects_score_outside_range_and_dead_letters(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    write_inbox(landing, review())
    settings = WorkerSettings(landing_dir=landing, max_tries=3)
    bad = dict(GOOD, sentiment_score=2)
    client = client_returning(bad)

    assert run_once(settings, client) == 0
    assert (landing / "processing" / "abc123.json").exists()
    assert (landing / "processing" / "abc123.tries").read_text(encoding="utf-8") == "1"

    run_once(settings, client)
    run_once(settings, client)

    assert (landing / "failed" / "abc123.json").exists()
    assert "model JSON rejected" in (landing / "failed" / "abc123.error.txt").read_text(encoding="utf-8")
    assert list((landing / "enrichments").glob("*.parquet")) == []


def test_recovers_file_left_in_processing(tmp_path: Path) -> None:
    landing = tmp_path / "landing"
    processing = landing / "processing"
    processing.mkdir(parents=True)
    (processing / "abc123.json").write_text(json.dumps(review()), encoding="utf-8")

    written = run_once(WorkerSettings(landing_dir=landing), client_returning(GOOD))

    assert written == 1
    assert (landing / "done" / "abc123.json").exists()
