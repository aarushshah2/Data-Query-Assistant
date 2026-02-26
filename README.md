# Data-Query-Assistant
AI-powered natural language interface for PostgreSQL — ask questions in plain English, get instant results. Runs 100% locally with Ollama.
The idea: non-technical teams shouldn't need to know SQL to get answers from a database.

What it does:
→ You type a question in plain English
→ A local AI model converts it to SQL
→ The query runs safely on PostgreSQL
→ Results appear instantly in a chat interface

Built with Python, Streamlit, PostgreSQL, and Ollama (fully local — no API keys, no data leaving your machine).

Key things I focused on:
→ Security (SELECT-only, read-only transactions, restricted table blocklist)
→ Clean modular architecture
→ Support for uploading your own CSV/Excel data
→ Audit logging on every query
