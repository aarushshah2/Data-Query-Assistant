# 🤖 Intelligent Data Query Assistant (Local — Ollama)

A production-ready AI-powered system that lets non-technical users query PostgreSQL databases using plain English — **100% local, no API keys, no cloud**.

---

## 📁 Project Structure

```
query_assistant/
├── core/
│   ├── __init__.py
│   ├── config.py           # Environment & settings
│   ├── database.py         # PostgreSQL connection pool
│   ├── schema_inspector.py # Introspects DB schema for AI context
│   ├── nl_to_sql.py        # Ollama: NL → SQL (local LLM)
│   ├── sql_validator.py    # Safety validation layer
│   ├── query_executor.py   # Safe query execution
│   └── logger.py           # Query audit logger
├── api/
│   ├── __init__.py
│   └── query_handler.py    # Orchestrates the full pipeline
├── ui/
│   └── app.py              # Streamlit chatbot UI
├── migrations/
│   └── init.sql            # DB schema + sample data
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Install Ollama
```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download from https://ollama.com/download
```

### 2. Pull a model (choose one)
```bash
ollama pull llama3.1          # Recommended — best SQL quality (~4.7 GB)
ollama pull codellama         # Code-focused alternative (~3.8 GB)
ollama pull mistral           # Lighter option (~4.1 GB)
ollama pull qwen2.5-coder     # Excellent for SQL (~4.7 GB)
```

### 3. Start Ollama
```bash
ollama serve
# Runs on http://localhost:11434 by default
```

### 4. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env — set your DB credentials and model name
```

### 6. Initialize database
```bash
psql -U your_user -d your_db -f migrations/init.sql
```

### 7. Run the app
```bash
streamlit run ui/app.py
```

---

## 🦙 Recommended Models (best → lightest)

| Model | Pull command | Size | SQL Quality |
|---|---|---|---|
| `llama3.1` | `ollama pull llama3.1` | 4.7 GB | ⭐⭐⭐⭐⭐ |
| `qwen2.5-coder` | `ollama pull qwen2.5-coder` | 4.7 GB | ⭐⭐⭐⭐⭐ |
| `codellama` | `ollama pull codellama` | 3.8 GB | ⭐⭐⭐⭐ |
| `mistral` | `ollama pull mistral` | 4.1 GB | ⭐⭐⭐⭐ |
| `phi3` | `ollama pull phi3` | 2.3 GB | ⭐⭐⭐ |

Set your choice in `.env`:
```
OLLAMA_MODEL=llama3.1
```

The **sidebar in the UI** also lets you switch models on the fly from whatever you have pulled.

---

## 🔐 Security Features

| Feature | Description |
|---|---|
| SELECT-only enforcement | Blocks INSERT, UPDATE, DELETE, DROP, ALTER |
| Multi-statement prevention | Blocks semicolon-separated chained queries |
| Restricted table blocklist | Prevents access to `query_logs`, `users`, `secrets` |
| Automatic LIMIT injection | Caps results at 500 rows if no LIMIT specified |
| Read-only DB transaction | Even if validation fails, PostgreSQL rejects writes |
| Schema-aware AI | AI only sees real tables/columns — no hallucinations |
| 100% local | No data leaves your machine |

---

## 🧪 Example Questions

- "Show me leads from Texas created in the last 7 days"
- "How many customers signed up this month?"
- "List vehicles that are not running"
- "Show top 10 states by number of leads"
- "What is the average deal value by sales rep?"

---

## 🏗️ Architecture

```
User Question
     ↓
[Schema Inspector] → loads real table/column context
     ↓
[NL → SQL (Ollama local LLM)] → generates PostgreSQL SELECT
     ↓
[SQL Validator] → safety checks, LIMIT injection
     ↓
[Query Executor] → runs in READ ONLY transaction, times execution
     ↓
[Audit Logger] → stores question, SQL, timing to DB
     ↓
[Streamlit UI] → displays results in chatbot format
```

