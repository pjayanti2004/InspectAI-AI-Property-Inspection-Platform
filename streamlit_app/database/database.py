"""Database connection management for InspectAI.

Wraps Python's built-in sqlite3 module with a thin helper that:
  • Opens a WAL-mode connection to a file-based SQLite database.
  • Registers adapters for common Python types.
  • Exposes a factory for row-factory (dict-like access).
  • Provides a context-managed ``get_connection()`` helper.

No ORM.  No external dependencies.  Thread-safe via per-thread connections.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from streamlit_app.utils.exceptions import DatabaseError
from streamlit_app.utils.logger import get_logger

# ── Logging ──────────────────────────────────────────────────────────────────

_logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

import os as _os
_DB_PATH_ENV = _os.getenv("DATABASE_PATH", "")

if _DB_PATH_ENV:
    DB_PATH: Path = Path(_DB_PATH_ENV)
else:
    DB_PATH: Path = Path(__file__).resolve().parent / "inspectai.db"

# ── Per-thread connection cache ───────────────────────────────────────────────

_thread_local = threading.local()


# ── ConnectionManager (backwards-compatible shim) ─────────────────────────────
# Deprecated: use get_connection() directly.  Kept for imports from
# database/__init__.py and legacy code.

class ConnectionManager:
    """Backwards-compatible wrapper around get_connection().

    .. deprecated::
        Use :func:`get_connection` directly instead.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Return a thread-local connection (same as get_connection())."""
        return get_connection()

    def close(self) -> None:
        """Close the current thread's connection."""
        close_connection()


# ── Row factory ───────────────────────────────────────────────────────────────

def _dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict[str, object]:
    """Return each row as a dict keyed by column name."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# ── Connection helper ─────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Open (or return) a thread-local SQLite connection.

    Uses WAL journal mode for better concurrent reads and
    ``detect_types=sqlite3.PARSE_DECLTYPES`` for automatic type conversion.
    """
    cached = getattr(_thread_local, "connection", None)
    if cached is not None:
        try:
            cached.execute("SELECT 1")
            return cached
        except sqlite3.Error:
            _thread_local.connection = None

    try:
        conn = sqlite3.connect(
            str(DB_PATH),
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        conn.row_factory = _dict_factory
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA cache_size=-64000")  # 64 MB cache
        conn.execute("PRAGMA mmap_size=268435456")  # 256 MB mmap
        conn.execute("PRAGMA synchronous=NORMAL")   # safe with WAL
        conn.execute("PRAGMA temp_store=MEMORY")    # temp tables in RAM
        conn.execute("PRAGMA page_size=4096")       # optimal for most OS
        _thread_local.connection = conn
        _logger.debug("Opened new SQLite connection (thread=%s).", threading.current_thread().name)
        return conn
    except sqlite3.Error as exc:
        _logger.exception("Failed to open database connection.")
        raise DatabaseError(
            f"Could not connect to database at '{DB_PATH}'.",
            details={"path": str(DB_PATH), "error": str(exc)},
        ) from exc


def close_connection() -> None:
    """Close the current thread's cached connection, if any."""
    conn = getattr(_thread_local, "connection", None)
    if conn is not None:
        try:
            conn.close()
        except sqlite3.Error as exc:
            _logger.warning("Error closing connection: %s", exc)
        _thread_local.connection = None
        _logger.debug("Closed SQLite connection.")


def init_db() -> None:
    """Create all tables if they don't exist (idempotent)."""
    from streamlit_app.database.schema import ALL_SCHEMA_STATEMENTS, CREATE_TABLE_MIGRATIONS

    conn = get_connection()
    try:
        # Apply schema
        for stmt in ALL_SCHEMA_STATEMENTS:
            conn.execute(stmt)

        # Migration tracking table
        conn.execute(CREATE_TABLE_MIGRATIONS)

        # Record current version (version 1 = initial schema)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version) VALUES(1)"
        )
        conn.commit()
        _logger.info("Database initialised (version 1).")
    except sqlite3.Error as exc:
        conn.rollback()
        _logger.exception("Database initialisation failed.")
        raise DatabaseError(
            "Failed to initialise database schema.",
            details={"error": str(exc)},
        ) from exc


def get_db_version() -> int:
    """Return the highest applied migration version."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT MAX(version) as v FROM schema_migrations"
        ).fetchone()
        return row["v"] if row and row["v"] is not None else 0
    except sqlite3.Error as exc:
        _logger.exception("Failed to read database version.")
        raise DatabaseError(
            "Could not read schema_migrations table.",
            details={"error": str(exc)},
        ) from exc


def reset_db() -> None:
    """Drop all tables and re-create from scratch.

    **Use only in development/testing.**  Destroys all data.
    """
    from streamlit_app.database.schema import ALL_SCHEMA_STATEMENTS, CREATE_TABLE_MIGRATIONS

    conn = get_connection()
    try:
        # Drop in reverse order (children before parents)
        conn.execute("DROP TABLE IF EXISTS reports")
        conn.execute("DROP TABLE IF EXISTS inspection_images")
        conn.execute("DROP TABLE IF EXISTS inspections")
        conn.execute("DROP TABLE IF EXISTS properties")
        conn.execute("DROP TABLE IF EXISTS schema_migrations")
        conn.commit()

        # Re-create
        for stmt in ALL_SCHEMA_STATEMENTS:
            conn.execute(stmt)
        conn.execute(CREATE_TABLE_MIGRATIONS)
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version) VALUES(1)"
        )
        conn.commit()
        _logger.warning("Database reset — all data destroyed.")
    except sqlite3.Error as exc:
        conn.rollback()
        _logger.exception("Database reset failed.")
        raise DatabaseError(
            "Failed to reset database.",
            details={"error": str(exc)},
        ) from exc


# ── Context manager ───────────────────────────────────────────────────────────

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager that yields a connection and handles commit/rollback.

    Usage::

        with get_db() as conn:
            conn.execute("SELECT * FROM properties")
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
