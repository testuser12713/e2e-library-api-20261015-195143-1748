import hmac

from fastapi import Depends, Header, Security
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings
from app.errors import ApiError

# Documents the X-API-Key scheme in /docs; the check itself is require_api_key.
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = settings.library_api_key
    if not expected:
        raise ApiError(503, "api_key_not_configured", "API key is not configured on the server")
    if x_api_key is None or not hmac.compare_digest(
        x_api_key.encode("utf-8"), expected.encode("utf-8")
    ):
        raise ApiError(401, "unauthorized", "Missing or invalid API key")


# Dependencies for every POST/PUT/PATCH/DELETE route.
WRITE_DEPENDENCIES = [Security(api_key_scheme), Depends(require_api_key)]
