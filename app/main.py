from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import health
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.infrastructure.database.session import engine
from app.infrastructure.middleware.rate_limit import limiter
from app.infrastructure.middleware.request_id import RequestIDMiddleware
from app.infrastructure.middleware.security_headers import SecurityHeadersMiddleware

configure_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.started", env=settings.environment)
    yield
    await engine.dispose()
    logger.info("app.stopped")


_is_prod = settings.environment == "production"

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

# Middleware wrap requests outermost → innermost in reverse registration order.
# We want: CORS (outer) → SecurityHeaders → RequestID (inner), so CORS headers are
# present even on error responses. add_middleware prepends, so register inner first.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # explicit allowlist, never "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _envelope(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=_envelope(exc.code, exc.message, exc.details))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=_envelope("VALIDATION_ERROR", "Request failed validation", {"errors": exc.errors()}),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=_envelope("HTTP_ERROR", str(exc.detail)))


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internals to the client, even in debug — debug=True only affects
    # uvicorn/FastAPI's own tracebacks in logs, not what's sent over the wire here.
    logger.error("unhandled_exception", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("INTERNAL_ERROR", "An unexpected error occurred"),
    )


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Boilerplate", "docs": "/docs"}


app.include_router(health.router)
app.include_router(api_router)
