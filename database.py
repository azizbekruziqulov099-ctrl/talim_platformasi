"""Bounded, leak-safe PostgreSQL connections for modular endpoints.

Legacy ``main.py`` still opens one connection per request. New modules use this
pool so they can be migrated independently without changing working legacy
routes in one risky rewrite.
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Iterator

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool


class DatabaseBusyError(RuntimeError):
    """Raised when every configured database connection is busy."""


_pool: ThreadedConnectionPool | None = None
_pool_guard = threading.Lock()
_slot_guard: threading.BoundedSemaphore | None = None


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _get_pool() -> tuple[ThreadedConnectionPool, threading.BoundedSemaphore]:
    global _pool, _slot_guard
    if _pool is not None and _slot_guard is not None:
        return _pool, _slot_guard

    with _pool_guard:
        if _pool is None:
            database_url = os.getenv("DATABASE_URL", "").strip()
            if not database_url:
                raise RuntimeError("DATABASE_URL sozlanmagan")

            minimum = _int_env("DB_POOL_MIN", 1, 1, 20)
            maximum = _int_env("DB_POOL_MAX", 10, minimum, 100)
            statement_timeout = _int_env(
                "DB_STATEMENT_TIMEOUT_MS", 15_000, 1_000, 120_000
            )
            lock_timeout = _int_env(
                "DB_LOCK_TIMEOUT_MS", 5_000, 500, 60_000
            )
            _pool = ThreadedConnectionPool(
                minimum,
                maximum,
                dsn=database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=_int_env("DB_CONNECT_TIMEOUT", 10, 2, 60),
                application_name="samtm-modular-api",
                options=(
                    f"-c statement_timeout={statement_timeout} "
                    f"-c lock_timeout={lock_timeout} "
                    "-c idle_in_transaction_session_timeout=30000 "
                    "-c timezone=Asia/Tashkent"
                ),
            )
            _slot_guard = threading.BoundedSemaphore(maximum)

    return _pool, _slot_guard


@contextmanager
def db_session(*, readonly: bool = False) -> Iterator[tuple[object, object]]:
    """Yield ``(connection, cursor)`` and always return the connection.

    A semaphore makes pool exhaustion wait briefly instead of failing
    immediately. Every exception rolls the transaction back; every path closes
    the cursor and returns (or discards) the connection.
    """

    pool, slots = _get_pool()
    wait_seconds = _int_env("DB_POOL_WAIT_SECONDS", 8, 1, 60)
    if not slots.acquire(timeout=wait_seconds):
        raise DatabaseBusyError(
            "Baza hozir band. Bir necha soniyadan keyin qayta urinib ko'ring."
        )

    connection = None
    cursor = None
    discard = False
    try:
        connection = pool.getconn()
        connection.autocommit = False
        cursor = connection.cursor()
        if readonly:
            cursor.execute("SET TRANSACTION READ ONLY")
        yield connection, cursor
        if readonly:
            connection.rollback()
        else:
            connection.commit()
    except Exception:
        if connection is not None and not connection.closed:
            try:
                connection.rollback()
            except Exception:
                discard = True
        raise
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                discard = True
        if connection is not None:
            if connection.closed:
                discard = True
            try:
                pool.putconn(connection, close=discard)
            except Exception:
                try:
                    connection.close()
                except Exception:
                    pass
        slots.release()


def close_pool() -> None:
    """Close all pooled connections during an orderly process shutdown."""

    global _pool, _slot_guard
    with _pool_guard:
        if _pool is not None:
            _pool.closeall()
        _pool = None
        _slot_guard = None
