"""
database.py - Thread-safe PostgreSQL connection pool.
"""
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from core.config import settings


_pool: pool.ThreadedConnectionPool | None = None


def get_pool() -> pool.ThreadedConnectionPool:
    """Lazily create the connection pool (singleton)."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=10,
            options=f"-c statement_timeout={settings.QUERY_TIMEOUT * 1000}",  # ms
        )
    return _pool


@contextmanager
def get_connection():
    """Context manager that yields a connection and returns it to the pool."""
    conn_pool = get_pool()
    conn = conn_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn_pool.putconn(conn)


def test_connection() -> tuple[bool, str]:
    """Check DB connectivity. Returns (ok, message)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)
