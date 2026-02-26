"""
sql_validator.py - Multi-layer SQL safety validation.

Validates that the generated SQL is:
  1. A single SELECT statement only
  2. Not accessing restricted tables
  3. Under the row limit (injects LIMIT if missing)
"""
from __future__ import annotations
import re
import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DDL, DML
from core.config import settings


# ── Dangerous keyword patterns ─────────────────────────────────────────────
_DANGEROUS_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|"
    r"GRANT|REVOKE|EXEC|EXECUTE|CALL|COPY|LOAD|IMPORT|EXPORT|"
    r"pg_read_file|pg_write_file|lo_import|lo_export|DBLINK)\b",
    re.IGNORECASE,
)

# Match any attempt to start a second statement after a semicolon
_MULTI_STATEMENT_PATTERN = re.compile(r";.+", re.DOTALL)

# Detect LIMIT clause already present
_LIMIT_PATTERN = re.compile(r"\bLIMIT\s+\d+\b", re.IGNORECASE)


class ValidationResult:
    def __init__(self, valid: bool, sql: str | None = None, reason: str | None = None):
        self.valid = valid
        self.sql = sql            # possibly modified (LIMIT injected)
        self.reason = reason      # human-readable rejection reason

    def __repr__(self):
        return f"ValidationResult(valid={self.valid}, reason={self.reason!r})"


def validate_sql(sql: str) -> ValidationResult:
    """
    Full safety validation pipeline.
    Returns a ValidationResult with the (possibly modified) safe SQL or a reason for rejection.
    """
    sql = sql.strip()

    # ── 1. Basic non-empty check ───────────────────────────────────────────
    if not sql:
        return ValidationResult(False, reason="Empty query received.")

    # ── 2. Dangerous keyword scan ──────────────────────────────────────────
    match = _DANGEROUS_PATTERN.search(sql)
    if match:
        return ValidationResult(
            False,
            reason=f"Forbidden keyword detected: '{match.group()}'. Only SELECT queries are allowed."
        )

    # ── 3. Multi-statement prevention ─────────────────────────────────────
    # Strip trailing semicolons then check for embedded ones
    cleaned = sql.rstrip(";").strip()
    if ";" in cleaned:
        return ValidationResult(
            False,
            reason="Multiple SQL statements detected. Only a single SELECT is allowed."
        )

    # ── 4. Parse with sqlparse and verify first token is SELECT ───────────
    try:
        statements = sqlparse.parse(cleaned)
    except Exception:
        return ValidationResult(False, reason="SQL parsing failed.")

    if not statements or not statements[0].tokens:
        return ValidationResult(False, reason="Could not parse SQL statement.")

    stmt: Statement = statements[0]
    first_meaningful = next(
        (t for t in stmt.tokens if not t.is_whitespace), None
    )

    if first_meaningful is None or first_meaningful.ttype not in (DML,):
        # Fallback: check raw string starts with SELECT
        if not cleaned.upper().lstrip().startswith("SELECT"):
            return ValidationResult(
                False,
                reason="Only SELECT queries are permitted."
            )
    else:
        if first_meaningful.normalized.upper() != "SELECT":
            return ValidationResult(
                False,
                reason=f"Query must start with SELECT. Got: '{first_meaningful.normalized}'."
            )

    # ── 5. Restricted table check ──────────────────────────────────────────
    sql_upper = cleaned.upper()
    for restricted in settings.RESTRICTED_TABLES:
        # Match whole word to avoid partial matches
        if re.search(rf"\b{restricted.upper()}\b", sql_upper):
            return ValidationResult(
                False,
                reason=f"Access to restricted table '{restricted}' is not allowed."
            )

    # ── 6. Inject LIMIT if missing ─────────────────────────────────────────
    if not _LIMIT_PATTERN.search(cleaned):
        cleaned = f"{cleaned}\nLIMIT {settings.MAX_ROWS}"

    return ValidationResult(True, sql=cleaned)
