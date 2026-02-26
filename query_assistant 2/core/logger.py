"""
logger.py - Stores every query attempt in the query_logs audit table.
Uses a separate connection to avoid interfering with read-only sessions.
"""
from __future__ import annotations
import psycopg2
from core.config import settings


def log_query(
    *,
    user_question: str,
    generated_sql: str | None,
    validation_passed: bool,
    execution_time_ms: float | None = None,
    row_count: int | None = None,
    error_message: str | None = None,
) -> None:
    """
    Insert an audit record into query_logs.
    Silently swallows errors so logging never crashes the main pipeline.
    """
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=5,
        )
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO query_logs
                        (user_question, generated_sql, validation_passed,
                         execution_time_ms, row_count, error_message)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_question,
                        generated_sql,
                        validation_passed,
                        execution_time_ms,
                        row_count,
                        error_message,
                    ),
                )
        conn.close()
    except Exception:
        pass  # Logging must never crash the app
