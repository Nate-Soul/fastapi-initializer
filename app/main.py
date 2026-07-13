from fastapi import FastAPI

from app.api import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.events import lifespan
from app.core.logging import configure_logging, get_logger
from app.infrastructure.middleware.cors import configure_cors
from app.infrastructure.middleware.error_handler import register_exception_handlers
from app.infrastructure.middleware.rate_limit import limiter
from app.infrastructure.middleware.request_id import RequestIDMiddleware
from app.infrastructure.middleware.security_headers import SecurityHeadersMiddleware

configure_logging()
logger = get_logger(__name__)
settings = get_settings()

_is_prod = settings.environment == "production"

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)

app.state.limiter = limiter

# Middleware wrap requests outermost → innermost in reverse registration order.
# We want: CORS (outer) → SecurityHeaders → RequestID (inner), so CORS headers are
# present even on error responses. add_middleware prepends, so register inner first.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
configure_cors(app)  # added last → outermost

register_exception_handlers(app)


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Boilerplate", "docs": "/docs"}


app.include_router(health.router)
app.include_router(api_router)
