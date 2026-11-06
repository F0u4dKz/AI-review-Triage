from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Safe as a single path segment: no slashes, no "..".
REVIEW_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"


class ReviewIn(BaseModel):
    """Webhook body. Matches the review contract the generator already sends."""

    review_id: str = Field(pattern=REVIEW_ID_PATTERN)
    source: str = Field(min_length=1)
    order_id: int
    client_id: int
    product_id: int
    rating: int = Field(ge=1, le=5)
    text: str = Field(min_length=1)
    created_at: datetime


class ReviewAccepted(BaseModel):
    review_id: str
    status: Literal["accepted"] = "accepted"
