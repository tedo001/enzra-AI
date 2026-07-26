"""Structured logging setup using structlog.

Produces human-friendly console logs in development and JSON logs in
production, so the same events are easy to read locally and easy to ship to a
log aggregator in the cloud.
"""

from __future__ import annotations

import logging
import sys

import structlog


def _console_renderer() -> structlog.dev.ConsoleRenderer:
    """Return a console renderer, preferring colours when supported.

    On Windows, structlog's coloured output requires the optional ``colorama``
    package and raises ``SystemError`` without it. We degrade to plain output
    rather than crash, so the app runs everywhere out of the box.
    """
    try:
        return structlog.dev.ConsoleRenderer(colors=True)
    except SystemError:
        return structlog.dev.ConsoleRenderer(colors=False)


def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configure standard logging + structlog processors.

    Parameters
    ----------
    level:
        Root log level name (e.g. ``"INFO"``).
    json_logs:
        When ``True`` emit machine-readable JSON (recommended in production).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        timestamper,
    ]

    renderer = (
        structlog.processors.JSONRenderer() if json_logs else _console_renderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy) through structlog formatting.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
