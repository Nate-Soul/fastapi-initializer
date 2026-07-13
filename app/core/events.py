"""Application lifecycle: the ASGI ``lifespan`` context manager plus the startup and
shutdown hooks it runs.

Deliberately minimal today — startup just logs, shutdown disposes the DB engine's
connection pool. It is shaped to grow: add a resource (Redis, a task queue, a model
warm-up) as its own step inside ``_startup`` / ``_shutdown``. Follow the reference
services' convention and make optional resources *fail open* — wrap the step in
try/except and log, so one unavailable dependency degrades a feature instead of
blocking the whole app from booting. Anything the app genuinely cannot run without
should raise and abort startup instead.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.session import engine

logger = get_logger(__name__)
settings = get_settings()


async def _startup() -> None:
    logger.info("app.started", env=settings.environment)
    # Add startup steps here (e.g. cache connect, scheduler start, model warm-up).


async def _shutdown() -> None:
    # Add teardown steps here (mirror the startup steps, in reverse) before the engine
    # is disposed. Dispose the pool last so nothing tries to use it after it's gone.
    await engine.dispose()
    logger.info("app.stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bind to FastAPI via ``FastAPI(lifespan=lifespan)``. The try/finally guarantees
    shutdown runs even if the server is torn down after an error while serving."""
    await _startup()
    try:
        yield
    finally:
        await _shutdown()
