"""
nl_to_sql.py - Converts natural language questions into PostgreSQL
SELECT queries using a local Ollama model (e.g. llama3, codellama, mistral).
"""
from __future__ import annotations
import re
import requests
from core.config import settings
from core.schema_inspector import get_schema_context


_SYSTEM_PROMPT = """You are an expert PostgreSQL query generator for a business intelligence system.

Your ONLY job is to convert natural language questions into valid PostgreSQL SELECT queries.

STRICT RULES:
1. Output ONLY the raw SQL query — no markdown, no backticks, no explanation, no commentary.
2. Only generate SELECT statements. Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, GRANT, REVOKE, or any DDL/DML.
3. Never reference tables not listed in the schema below.
4. Use standard PostgreSQL syntax (e.g., NOW(), INTERVAL, DATE_TRUNC).
5. Always use table aliases for clarity in JOINs.
6. Prefer explicit column names over SELECT *.
7. If the question is ambiguous, make a reasonable business assumption.
8. If the question cannot be answered with the available schema, output exactly: CANNOT_ANSWER

{schema}"""


def convert_to_sql(question: str) -> dict:
    """
    Convert a natural language question to a SQL query via Ollama.

    Returns:
        {
            "sql": str | None,
            "can_answer": bool,
            "error": str | None,
        }
    """
    schema_context = get_schema_context()
    system = _SYSTEM_PROMPT.format(schema=schema_context)

    payload = {
        "model": settings.OLLAMA_MODEL,
        "system": system,
        "prompt": question,
        "stream": False,
        "options": {
            "temperature": 0,        # deterministic — critical for SQL
            "num_predict": 1024,
        },
    }

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120,             # local models can be slow on first call
        )
        response.raise_for_status()
        data = response.json()
        raw: str = data.get("response", "").strip()

        # Strip accidental markdown code fences that some models add
        raw = re.sub(r"^```(?:sql)?", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(r"```$", "", raw).strip()
        # Remove any leading/trailing blank lines
        raw = "\n".join(line for line in raw.splitlines() if line.strip())

        if not raw:
            return {"sql": None, "can_answer": False,
                    "error": "The model returned an empty response. Try rephrasing your question."}

        if raw.upper().strip() == "CANNOT_ANSWER":
            return {"sql": None, "can_answer": False, "error": None}

        return {"sql": raw, "can_answer": True, "error": None}

    except requests.exceptions.ConnectionError:
        return {
            "sql": None,
            "can_answer": False,
            "error": (
                f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. "
                "Make sure Ollama is running: `ollama serve`"
            ),
        }
    except requests.exceptions.Timeout:
        return {"sql": None, "can_answer": False,
                "error": "Ollama request timed out. The model may still be loading — try again."}
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "sql": None,
                "can_answer": False,
                "error": (
                    f"Model '{settings.OLLAMA_MODEL}' not found. "
                    f"Pull it first: `ollama pull {settings.OLLAMA_MODEL}`"
                ),
            }
        return {"sql": None, "can_answer": False, "error": f"Ollama HTTP error: {e}"}
    except Exception as e:
        return {"sql": None, "can_answer": False, "error": f"AI error: {str(e)}"}
