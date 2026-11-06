"""Land one review as landing/inbox/{review_id}.json.

A review_id already present in inbox, processing, done, or failed is a duplicate.
The JSON is written to a temp file in inbox, then os.link publishes it under the
final name. link fails if that name exists, so two concurrent posts cannot both win.
"""

import json
import os
import re
import uuid
from pathlib import Path

from api.schemas.review import REVIEW_ID_PATTERN, ReviewIn

LANDING_STATES = ("inbox", "processing", "done", "failed")

_REVIEW_ID = re.compile(REVIEW_ID_PATTERN)


class DuplicateReviewError(Exception):
    def __init__(self, review_id: str) -> None:
        self.review_id = review_id
        super().__init__(review_id)


class UnsafeReviewIdError(Exception):
    def __init__(self, review_id: str) -> None:
        self.review_id = review_id
        super().__init__(review_id)


def accept_review(review: ReviewIn, landing_dir: Path) -> None:
    if _REVIEW_ID.fullmatch(review.review_id) is None:
        raise UnsafeReviewIdError(review.review_id)

    filename = f"{review.review_id}.json"
    for state in LANDING_STATES:
        if (landing_dir / state / filename).exists():
            raise DuplicateReviewError(review.review_id)

    inbox = landing_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    temporary = inbox / f".{review.review_id}.{uuid.uuid4().hex}.tmp"
    temporary.write_text(
        json.dumps(review.model_dump(mode="json"), ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        os.link(temporary, inbox / filename)
    except FileExistsError as exc:
        raise DuplicateReviewError(review.review_id) from exc
    finally:
        temporary.unlink(missing_ok=True)
