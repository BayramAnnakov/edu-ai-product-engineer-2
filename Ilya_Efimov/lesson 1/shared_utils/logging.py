from __future__ import annotations

"""Centralized logging configuration for the Windsurf Summarization Agent."""

import logging
import sys
from typing import Optional


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def init_logging(level: str | int = "INFO") -> None:  # noqa: D401
    """Initialize root logger.

    This should be called once at application startup before any logging occurs.
    """
    root_logger = logging.getLogger()

    # Avoid adding handlers multiple times in interactive/long-running sessions
    if root_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger.addHandler(handler)

    root_logger.setLevel(level)


def get_logger(name: Optional[str] = None) -> logging.Logger:  # noqa: D401
    """Get a module-level logger; lazily initialize global configuration."""

    init_logging()
    return logging.getLogger(name)
