"""
config.py - Centralised settings loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── Database ──────────────────────────────────────────────
    DB_HOST: str     = os.getenv("DB_HOST", "localhost")
    DB_PORT: int     = int(os.getenv("DB_PORT", 5432))
    DB_NAME: str     = os.getenv("DB_NAME", "")
    DB_USER: str     = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    # ── Ollama (local LLM) ────────────────────────────────────
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str    = os.getenv("OLLAMA_MODEL", "llama3.1")

    # ── Query limits ──────────────────────────────────────────
    MAX_ROWS: int        = int(os.getenv("MAX_ROWS", 500))
    QUERY_TIMEOUT: int   = int(os.getenv("QUERY_TIMEOUT", 30))   # seconds

    # ── Tables the AI must never touch ────────────────────────
    RESTRICTED_TABLES: set = {"query_logs", "users", "secrets", "passwords", "api_keys"}


settings = Settings()
