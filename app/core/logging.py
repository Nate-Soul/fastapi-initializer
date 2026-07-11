"""Structured logging configuration (structlog).

Call ``configure_logging()`` once at startup. Use ``get_logger(__name__)`` to get a
bound logger. Output is human-friendly console rendering in dev and JSON in
production (toggled by ``settings.log_json``). The ``request_id`` bound by
``RequestIDMiddleware`` is merged into every log line automatically.
"""

import logging
import sys

import structlog
from structlog.typing import Processor

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy) through structlog's formatting so
    # everything shares one output format.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
