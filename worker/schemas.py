from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["delivery", "quality", "price", "support", "payment", "other"]
SentimentLabel = Literal["positive", "neutral", "negative"]


class ModelOutput(BaseModel):
    """What Ollama must return. Urgency is decided later in Python."""

    category: Category
    sentiment_score: float = Field(ge=-1, le=1)
    sentiment_label: SentimentLabel
    key_issues: list[str]


class Enrichment(BaseModel):
    review_id: str
    order_id: int
    client_id: int
    product_id: int
    rating: int = Field(ge=1, le=5)
    redacted_text: str
    category: Category
    sentiment_score: float = Field(ge=-1, le=1)
    sentiment_label: SentimentLabel
    key_issues: list[str]
    is_urgent: bool
    model_name: str
    processed_at: datetime
