"""
query_executor.py - Executes validated SQL queries and returns structured results.
"""
from __future__ import annotations
import time
import psycopg2
from core.database import get_connection


def execute_query(sql: str) -> dict:
    """
    Execute a (pre-validated) SQL query.

    Returns:
        {
            "success": bool,
            "rows": list[dict],
            "columns": list[str],
            "row_count": int,
            "execution_time_ms": float,
            "error": str | None,
        }
    """
    start = time.perf_counter()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows_raw = cur.fetchall()

        elapsed_ms = (time.perf_counter() - start) * 1000

        rows = [dict(zip(columns, row)) for row in rows_raw]

        return {
            "success": True,
            "rows": rows,
            "columns": columns,
            "row_count": len(rows),
            "execution_time_ms": round(elapsed_ms, 2),
            "error": None,
        }

    except psycopg2.errors.QueryCanceled:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": round(elapsed_ms, 2),
            "error": "Query timed out. Try a more specific question.",
        }
    except psycopg2.Error as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": round(elapsed_ms, 2),
            "error": f"Database error: {e.pgerror or str(e)}",
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "success": False,
            "rows": [],
            "columns": [],
            "row_count": 0,
            "execution_time_ms": round(elapsed_ms, 2),
            "error": f"Unexpected error: {str(e)}",
        }
