"""
schema_inspector.py - Reads the live PostgreSQL schema so the AI
only generates queries against real tables and columns.
"""
from __future__ import annotations
import functools
from core.database import get_connection
from core.config import settings


@functools.lru_cache(maxsize=1)
def get_schema_context() -> str:
    """
    Returns a compact, human-readable description of every non-restricted
    table in the database, including column names, types, and nullable flag.

    Result is cached for the lifetime of the process (restart to refresh).
    """
    schema: dict[str, list[dict]] = {}

    query = """
        SELECT
            c.table_name,
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            pgd.description AS column_comment
        FROM information_schema.columns c
        JOIN information_schema.tables t
            ON c.table_name = t.table_name
           AND c.table_schema = t.table_schema
        LEFT JOIN pg_catalog.pg_statio_all_tables st
            ON st.relname = c.table_name
        LEFT JOIN pg_catalog.pg_description pgd
            ON pgd.objoid = st.relid
           AND pgd.objsubid = c.ordinal_position
        WHERE c.table_schema = 'public'
          AND t.table_type = 'BASE TABLE'
        ORDER BY c.table_name, c.ordinal_position;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    for table_name, col_name, data_type, nullable, default, comment in rows:
        if table_name in settings.RESTRICTED_TABLES:
            continue
        schema.setdefault(table_name, []).append({
            "column": col_name,
            "type": data_type,
            "nullable": nullable == "YES",
        })

    if not schema:
        return "No accessible tables found."

    lines = ["Available database tables and columns:\n"]
    for table, columns in schema.items():
        lines.append(f"Table: {table}")
        for col in columns:
            nullable_str = "(nullable)" if col["nullable"] else ""
            lines.append(f"  - {col['column']} [{col['type']}] {nullable_str}")
        lines.append("")

    return "\n".join(lines)


def get_table_names() -> list[str]:
    """Returns list of accessible table names."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            )
            rows = cur.fetchall()
    return [r[0] for r in rows if r[0] not in settings.RESTRICTED_TABLES]
