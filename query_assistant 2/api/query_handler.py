"""
query_handler.py - Orchestrates the full NL → SQL → Execute → Log pipeline.

This is the single entry point called by the UI.
"""
from __future__ import annotations
from core.nl_to_sql import convert_to_sql
from core.sql_validator import validate_sql
from core.query_executor import execute_query
from core.logger import log_query


def handle_query(user_question: str) -> dict:
    """
    Full pipeline: question → SQL → validate → execute → log → return result.

    Return shape:
    {
        "success": bool,
        "user_question": str,
        "generated_sql": str | None,        # raw AI output
        "validated_sql": str | None,        # after safety checks & LIMIT injection
        "can_answer": bool,                  # False if schema can't answer the question
        "validation_passed": bool,
        "validation_error": str | None,
        "rows": list[dict],
        "columns": list[str],
        "row_count": int,
        "execution_time_ms": float | None,
        "error": str | None,                # user-facing error message
    }
    """
    result: dict = {
        "success": False,
        "user_question": user_question,
        "generated_sql": None,
        "validated_sql": None,
        "can_answer": True,
        "validation_passed": False,
        "validation_error": None,
        "rows": [],
        "columns": [],
        "row_count": 0,
        "execution_time_ms": None,
        "error": None,
    }

    # ── Step 1: NL → SQL ─────────────────────────────────────────────────
    nl_result = convert_to_sql(user_question)

    if nl_result["error"]:
        result["error"] = nl_result["error"]
        log_query(
            user_question=user_question,
            generated_sql=None,
            validation_passed=False,
            error_message=nl_result["error"],
        )
        return result

    if not nl_result["can_answer"]:
        result["can_answer"] = False
        result["error"] = (
            "I couldn't find relevant data in the database to answer that question. "
            "Try rephrasing or asking about leads, customers, vehicles, or deals."
        )
        log_query(
            user_question=user_question,
            generated_sql=None,
            validation_passed=False,
            error_message="Schema cannot answer question.",
        )
        return result

    result["generated_sql"] = nl_result["sql"]

    # ── Step 2: Validate ─────────────────────────────────────────────────
    validation = validate_sql(nl_result["sql"])
    result["validation_passed"] = validation.valid

    if not validation.valid:
        result["validation_error"] = validation.reason
        result["error"] = f"Query blocked: {validation.reason}"
        log_query(
            user_question=user_question,
            generated_sql=nl_result["sql"],
            validation_passed=False,
            error_message=validation.reason,
        )
        return result

    result["validated_sql"] = validation.sql

    # ── Step 3: Execute ──────────────────────────────────────────────────
    exec_result = execute_query(validation.sql)
    result["rows"] = exec_result["rows"]
    result["columns"] = exec_result["columns"]
    result["row_count"] = exec_result["row_count"]
    result["execution_time_ms"] = exec_result["execution_time_ms"]

    if exec_result["success"]:
        result["success"] = True
    else:
        result["error"] = exec_result["error"]

    # ── Step 4: Log ──────────────────────────────────────────────────────
    log_query(
        user_question=user_question,
        generated_sql=nl_result["sql"],
        validation_passed=True,
        execution_time_ms=exec_result["execution_time_ms"],
        row_count=exec_result["row_count"],
        error_message=exec_result["error"],
    )

    return result
