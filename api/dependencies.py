import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from api.config import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def require_api_key(
    request: Request,
    key: str | None = Depends(api_key_header),
) -> None:
    """Reject a missing or wrong X-API-Key with 401."""
    expected = request.app.state.settings.api_key
    if key is None or not secrets.compare_digest(key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
