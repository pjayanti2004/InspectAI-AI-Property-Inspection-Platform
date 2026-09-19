"""Logging configuration for InspectAI.

Sets up rotating file handlers for application and error logs,
plus convenience helpers used throughout the codebase.

Log files live in ``logs/`` (auto-created alongside this package).

Usage::

    from streamlit_app.utils.logger import get_logger, log_error, log_exception

    logger = get_logger(__name__)
    logger.info("Processing started")

    try:
        ...
    except SomeError as exc:
        log_exception(logger, "Failed to process image", exc)
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

# ── Paths ──────────────────────────────────────────────────────────────────────

_THIS_DIR = Path(__file__).resolve().parent
_APP_ROOT = _THIS_DIR.parent
_LOGS_DIR = _APP_ROOT / "logs"

# Ensure the logs directory exists
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

_APPLICATION_LOG = _LOGS_DIR / "application.log"
_ERROR_LOG = _LOGS_DIR / "error.log"

# ── Formatter ──────────────────────────────────────────────────────────────────

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

# ── Handlers ───────────────────────────────────────────────────────────────────

_application_handler = RotatingFileHandler(
    filename=str(_APPLICATION_LOG),
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8",
)
_application_handler.setLevel(logging.DEBUG)
_application_handler.setFormatter(_formatter)

_error_handler = RotatingFileHandler(
    filename=str(_ERROR_LOG),
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8",
)
_error_handler.setLevel(logging.ERROR)
_error_handler.setFormatter(_formatter)

# ── Console Handler ────────────────────────────────────────────────────────────

_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setLevel(logging.WARNING)
_console_handler.setFormatter(_formatter)

# ── Root Logger Configuration ──────────────────────────────────────────────────

_root_logger = logging.getLogger("inspectai")
_root_logger.setLevel(logging.DEBUG)
_root_logger.addHandler(_application_handler)
_root_logger.addHandler(_error_handler)
_root_logger.addHandler(_console_handler)
_root_logger.propagate = False

# ── Silence noisy third-party loggers ─────────────────────────────────────────

_noisy_loggers = [
    "PIL",
    "PIL.Image",
    "google",
    "google.generativeai",
    "httpx",
    "httpcore",
    "urllib3",
    "streamlit",
]

for _name in _noisy_loggers:
    _logger = logging.getLogger(_name)
    _logger.setLevel(logging.WARNING)
    _logger.propagate = False

# ── Public API ─────────────────────────────────────────────────────────────────


def configure_app_logging(namespace: str = "inspectai") -> logging.Logger:
    """Reconfigure the root logger for a specific app namespace.

    This is useful when switching between different InspectAI components
    that need separate log files or different log levels.

    Args:
        namespace: Logger namespace prefix.

    Returns:
        The configured root logger for the namespace.
    """
    logger = logging.getLogger(namespace)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(_application_handler)
        logger.addHandler(_error_handler)
        logger.addHandler(_console_handler)
    logger.propagate = False
    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``inspectai`` namespace.

    Args:
        name: Module name (typically ``__name__``).

    Returns:
        A ``logging.Logger`` instance configured with InspectAI handlers.
    """
    full_name = f"inspectai.{name}" if not name.startswith("inspectai") else name
    return logging.getLogger(full_name)


def log_info(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log an INFO-level message with optional extra context."""
    logger.info(message, extra=kwargs)


def log_warning(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log a WARNING-level message with optional extra context."""
    logger.warning(message, extra=kwargs)


def log_error(logger: logging.Logger, message: str, **kwargs: Any) -> None:
    """Log an ERROR-level message with optional extra context."""
    logger.error(message, extra=kwargs)


def log_exception(
    logger: logging.Logger,
    message: str,
    exc: BaseException,
    **kwargs: Any,
) -> None:
    """Log an ERROR with the full traceback of the exception.

    This is the preferred way to log caught exceptions.  It records the
    complete stack trace to both the application log and the dedicated
    error log file.

    Args:
        logger:     Logger instance.
        message:    Human-readable context string.
        exc:        The caught exception object.
        **kwargs:   Extra context fields.
    """
    exc_info = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(
        "%s\nException: %s\n%s",
        message,
        exc.__class__.__name__,
        exc_info,
        extra=kwargs,
    )


def shutdown_logging() -> None:
    """Flush and close all handlers.  Call on application shutdown."""
    for handler in _root_logger.handlers[:]:
        handler.flush()
        handler.close()
        _root_logger.removeHandler(handler)
    logging.shutdown()
