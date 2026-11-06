import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app

KEY = {"X-API-Key": "dev-key"}


@pytest.fixture
def landing(tmp_path: Path) -> Path:
    return tmp_path / "landing"


@pytest.fixture
def client(landing: Path) -> TestClient:
    app = create_app(Settings(api_key="dev-key", landing_dir=landing))
    with TestClient(app) as test_client:
        yield test_client


def payload(**overrides: object) -> dict:
    body = {
        "review_id": "abc123",
        "source": "shopify",
        "order_id": 1,
        "client_id": 2,
        "product_id": 3,
        "rating": 4,
        "text": "Très bien",
        "created_at": "2026-11-06T12:00:00",
    }
    body.update(overrides)
    return body


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_accepts_review(client: TestClient, landing: Path) -> None:
    response = client.post("/webhook/reviews", json=payload(), headers=KEY)
    assert response.status_code == 202
    assert response.json() == {"review_id": "abc123", "status": "accepted"}

    written = json.loads((landing / "inbox" / "abc123.json").read_text(encoding="utf-8"))
    assert written == {
        "review_id": "abc123",
        "source": "shopify",
        "order_id": 1,
        "client_id": 2,
        "product_id": 3,
        "rating": 4,
        "text": "Très bien",
        "created_at": "2026-11-06T12:00:00",
    }


def test_missing_api_key(client: TestClient, landing: Path) -> None:
    response = client.post("/webhook/reviews", json=payload())
    assert response.status_code == 401
    assert not (landing / "inbox" / "abc123.json").exists()


def test_wrong_api_key(client: TestClient) -> None:
    response = client.post("/webhook/reviews", json=payload(), headers={"X-API-Key": "nope"})
    assert response.status_code == 401


@pytest.mark.parametrize(
    "bad",
    [
        {"rating": 9},
        {"text": ""},
        {"review_id": "../etc/passwd"},
        {"review_id": "a/b"},
    ],
)
def test_rejects_invalid_payload(client: TestClient, landing: Path, bad: dict) -> None:
    response = client.post("/webhook/reviews", json=payload(**bad), headers=KEY)
    assert response.status_code == 422
    assert list((landing / "inbox").glob("*.json")) == []


def test_duplicate_in_inbox_keeps_first_file(client: TestClient, landing: Path) -> None:
    first = client.post("/webhook/reviews", json=payload(text="first"), headers=KEY)
    assert first.status_code == 202

    second = client.post("/webhook/reviews", json=payload(text="second"), headers=KEY)
    assert second.status_code == 409
    assert second.json()["detail"] == "duplicate review_id"

    written = json.loads((landing / "inbox" / "abc123.json").read_text(encoding="utf-8"))
    assert written["text"] == "first"


def test_duplicate_already_in_done(client: TestClient, landing: Path) -> None:
    (landing / "done" / "abc123.json").write_text("{}", encoding="utf-8")

    response = client.post("/webhook/reviews", json=payload(), headers=KEY)
    assert response.status_code == 409
    assert not (landing / "inbox" / "abc123.json").exists()
