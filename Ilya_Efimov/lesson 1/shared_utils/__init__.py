"""Shared utilities for Windsurf Summarization Agent."""

from .config import settings  # noqa: F401
from .logging import get_logger  # noqa: F401

__all__ = [
    "settings",
    "get_logger",
]
