"""
app.py - Streamlit chatbot UI for the Intelligent Data Query Assistant.

Run with:  streamlit run ui/app.py
"""
from __future__ import annotations
import sys
import os

# Make project root importable regardless of CWD
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import streamlit as st

from api.query_handler import handle_query
from core.database import test_connection
from core.schema_inspector import get_table_names
from core.schema_inspector import get_table_names
from core.file_importer import read_uploaded_file, import_dataframe_to_db

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Query Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        /* Chat bubbles */
        .user-bubble {
            background: #1e40af;
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
            margin: 8px 0 8px auto;
            max-width: 75%;
            width: fit-content;
            float: right;
            clear: both;
            font-size: 15px;
        }
        .ai-bubble {
            background: #1e293b;
            color: #e2e8f0;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            margin: 8px auto 8px 0;
            max-width: 75%;
            width: fit-content;
            float: left;
            clear: both;
            font-size: 15px;
        }
        .error-bubble {
            background: #7f1d1d;
            color: #fecaca;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            margin: 8px auto 8px 0;
            max-width: 75%;
            width: fit-content;
            float: left;
            clear: both;
            font-size: 14px;
        }
        .meta-row {
            clear: both;
            margin: 4px 0 16px 0;
            font-size: 12px;
            color: #64748b;
        }
        .clearfix { clear: both; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #0f172a;
        }
        section[data-testid="stSidebar"] * {
            color: #cbd5e1 !important;
        }

        /* Input row */
        .stTextInput > div > div > input {
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid #334155;
            border-radius: 12px;
            font-size: 15px;
        }
        .stButton > button {
            background: #1d4ed8;
            color: white;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            height: 42px;
        }
        .stButton > button:hover {
            background: #2563eb;
        }

        /* Chat container */
        .chat-container {
            max-height: 68vh;
            overflow-y: auto;
            padding: 8px 0;
        }

        /* Main background */
        .main .block-container {
            background: #0f172a;
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []   # list of dicts: {role, content, meta}
if "db_ok" not in st.session_state:
    st.session_state.db_ok = None


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 Query Assistant")
    st.markdown("Ask questions in plain English. The AI converts them to SQL and runs them safely.")
    # ── File Upload ───────────────────────────────────────────
    st.divider()
    st.markdown("### 📂 Upload Your Data")
    st.caption("Upload a CSV, TXT, or Excel file to query it instantly.")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "txt", "xlsx", "xls"],
        label_visibility="collapsed",
        key="file_uploader",
    )

    if uploaded_file:
        with st.spinner("Reading file..."):
            df_preview, read_err = read_uploaded_file(uploaded_file)

        if read_err:
            st.error(read_err)
        else:
            st.success(f"📄 {uploaded_file.name} — {len(df_preview):,} rows × {len(df_preview.columns)} cols")
            st.dataframe(df_preview.head(5), use_container_width=True, hide_index=True)

            default_name = uploaded_file.name.rsplit(".", 1)[0].lower().replace(" ", "_")
            table_name = st.text_input("Save as table name:", value=default_name, key="upload_table_name")

            mode = st.radio(
                "If table already exists:",
                ["Replace it", "Append to it"],
                horizontal=True,
                key="upload_mode",
            )

            if st.button("⬆️ Import to Database", use_container_width=True, key="do_import"):
                with st.spinner("Importing..."):
                    ok, msg = import_dataframe_to_db(
                        df_preview,
                        table_name,
                        if_exists="replace" if mode == "Replace it" else "append",
                    )
                    try:
                        from core.schema_inspector import get_schema_context
                        get_schema_context.cache_clear()
                    except Exception:
                        pass
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # Table list
    st.divider()

    # Ollama status
    st.markdown("### 🦙 Ollama Status")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Check Ollama", use_container_width=True):
            try:
                import requests as _req
                from core.config import settings as _s
                r = _req.get(f"{_s.OLLAMA_BASE_URL}/api/tags", timeout=3)
                models = [m["name"] for m in r.json().get("models", [])]
                st.session_state["ollama_ok"] = (True, models)
            except Exception as e:
                st.session_state["ollama_ok"] = (False, str(e))

    with col_b:
        if st.button("Test DB", use_container_width=True):
            ok, msg = test_connection()
            st.session_state.db_ok = (ok, msg)

    if "ollama_ok" in st.session_state:
        ok, payload = st.session_state["ollama_ok"]
        if ok:
            st.success(f"✅ Ollama running")
            if payload:
                from core.config import settings as _s
                current = _s.OLLAMA_MODEL
                # Let user pick a model from what's pulled
                chosen = st.selectbox("Active model", payload,
                                      index=payload.index(current) if current in payload else 0,
                                      key="model_picker")
                if chosen != _s.OLLAMA_MODEL:
                    _s.OLLAMA_MODEL = chosen
        else:
            st.error(f"❌ {payload}")
            st.caption("Run `ollama serve` to start Ollama.")

    if st.session_state.db_ok is not None:
        ok, msg = st.session_state.db_ok
        if ok:
            st.success(f"✅ DB connected")
        else:
            st.error(f"❌ DB: {msg}")

    # Table list
    st.divider()
    st.markdown("### 📋 Available Tables")
    try:
        tables = get_table_names()
        for t in tables:
            st.markdown(f"- `{t}`")
    except Exception:
        st.caption("Connect to DB to see tables.")

    st.divider()
    st.markdown("### 💡 Example Questions")
    examples = [
        "Show me leads from Texas created in the last 7 days",
        "How many customers signed up this month?",
        "List vehicles that are not running",
        "Show top 10 states by number of leads",
        "What is the total deal value per sales rep?",
        "Which customers are on the enterprise plan?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
            st.session_state["prefill"] = ex
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h2 style='color:#f1f5f9; margin-bottom:4px;'>🤖 Intelligent Data Query Assistant</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#94a3b8; margin-top:0;'>Ask questions in plain English — I'll query the database for you.</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Chat history ──────────────────────────────────────────────────────────────
chat_area = st.container()

with chat_area:
    if not st.session_state.messages:
        st.markdown(
            "<div style='text-align:center; color:#475569; padding:60px 0;'>"
            "No messages yet. Ask a question below to get started!"
            "</div>",
            unsafe_allow_html=True,
        )

    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        meta = msg.get("meta", {})

        if role == "user":
            st.markdown(
                f'<div class="user-bubble">🧑 {content}</div><div class="clearfix"></div>',
                unsafe_allow_html=True,
            )

        elif role == "assistant":
            if meta.get("error"):
                st.markdown(
                    f'<div class="error-bubble">⚠️ {meta["error"]}</div>'
                    '<div class="clearfix"></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="ai-bubble">✅ Query returned <strong>{meta.get("row_count", 0)}</strong> rows '
                    f'in <strong>{meta.get("execution_time_ms", 0):.1f}ms</strong></div>'
                    '<div class="clearfix"></div>',
                    unsafe_allow_html=True,
                )

            # SQL expander
            sql_to_show = meta.get("validated_sql") or meta.get("generated_sql")
            if sql_to_show:
                with st.expander("🔍 View Generated SQL", expanded=False):
                    st.code(sql_to_show, language="sql")

            # Results table
            if meta.get("rows"):
                df = pd.DataFrame(meta["rows"])
                # Convert any non-serialisable types to string
                for col in df.columns:
                    if df[col].dtype == object:
                        try:
                            df[col] = df[col].astype(str)
                        except Exception:
                            pass
                st.dataframe(df, use_container_width=True, hide_index=True)
            elif meta.get("success"):
                st.info("Query ran successfully but returned no rows.")


# ── Input area ────────────────────────────────────────────────────────────────
st.divider()

prefill = st.session_state.pop("prefill", "")

col1, col2 = st.columns([5, 1])
with col1:
    user_input = st.text_input(
        "Ask a question...",
        value=prefill,
        placeholder="e.g. Show me leads from Texas created in the last 7 days",
        label_visibility="collapsed",
        key="user_input",
    )
with col2:
    send_clicked = st.button("Send ➤", use_container_width=True)


def process_question(question: str):
    question = question.strip()
    if not question:
        return

    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    # Run pipeline
    with st.spinner("🤔 Thinking..."):
        result = handle_query(question)

    # Build assistant meta
    meta = {
        "generated_sql": result.get("generated_sql"),
        "validated_sql": result.get("validated_sql"),
        "rows": result.get("rows", []),
        "columns": result.get("columns", []),
        "row_count": result.get("row_count", 0),
        "execution_time_ms": result.get("execution_time_ms", 0),
        "success": result.get("success", False),
        "error": result.get("error"),
    }

    st.session_state.messages.append({
        "role": "assistant",
        "content": "",
        "meta": meta,
    })

    st.rerun()


if send_clicked and user_input:
    process_question(user_input)
elif prefill:
    process_question(prefill)
