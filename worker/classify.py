"""One chat call to the local Ollama server, then a Pydantic check of the JSON."""

import httpx
from pydantic import ValidationError

from worker.config import WorkerSettings
from worker.schemas import ModelOutput

_INSTRUCTIONS = """Triage this customer review.
category is the main issue: delivery, quality, price, support, payment, or other.
sentiment_label is positive, neutral, or negative.
sentiment_score runs from -1 (very negative) to 1 (very positive). It is not the star rating.
key_issues lists one to three short phrases that appear in the review.

Star rating: {rating}/5
Review:
{text}
"""


def classify(text: str, rating: int, settings: WorkerSettings, client: httpx.Client) -> ModelOutput:
    response = client.post(
        settings.ollama_url,
        timeout=settings.request_timeout,
        json={
            "model": settings.model_name,
            "stream": False,
            "format": ModelOutput.model_json_schema(),
            "options": {"temperature": 0},
            "messages": [{"role": "user", "content": _INSTRUCTIONS.format(rating=rating, text=text)}],
        },
    )
    response.raise_for_status()
    content = response.json()["message"]["content"]
    try:
        if isinstance(content, str):
            return ModelOutput.model_validate_json(content)
        return ModelOutput.model_validate(content)
    except ValidationError as exc:
        raise ValueError(f"model JSON rejected: {content}") from exc
