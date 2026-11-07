"""Urgency is a fixed rule. The model does not decide it."""

_KEYWORDS = ("refund", "lawyer", "never again")


def is_urgent(rating: int, sentiment_score: float, text: str) -> bool:
    if rating <= 2 and sentiment_score <= -0.6:
        return True
    lowered = text.lower()
    return any(keyword in lowered for keyword in _KEYWORDS)
