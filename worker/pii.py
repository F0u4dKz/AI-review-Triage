"""Replace emails and French phone numbers before the text reaches the model."""

import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+33[\s.-]?(?:\(0\)[\s.-]?)?|0)[1-9](?:[\s.-]?\d{2}){4}")


def redact(text: str) -> str:
    without_email = _EMAIL.sub("[EMAIL]", text)
    return _PHONE.sub("[PHONE]", without_email)
