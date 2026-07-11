"""Security headers middleware — applied to every response.

Closes the Arc ``backend-standards`` requirement for HSTS / X-Frame-Options /
X-Content-Type-Options / CSP. Headers set:
  - Content-Security-Policy   strict baseline for the API; relaxed for the docs UI
  - X-Frame-Options           DENY
  - X-Content-Type-Options    nosniff
  - Referrer-Policy           no-referrer
  - Permissions-Policy        minimal footprint
  - Strict-Transport-Security production only (HSTS)
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}

# CSP for the API itself — no browser rendering expected.
_API_CSP = "default-src 'none'; frame-ancestors 'none'"

# Relaxed CSP for Swagger UI / ReDoc (they load scripts/styles from the same origin).
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "frame-ancestors 'none'"
)

_PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every outgoing response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        csp = _DOCS_CSP if request.url.path in _DOCS_PATHS else _API_CSP
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = _PERMISSIONS_POLICY

        if get_settings().environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response
