from __future__ import annotations
import re
import io
import pandas as pd
import psycopg2.extras
from core.database import get_connection


def _sanitise_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    if not name or name[0].isdigit():
        name = "tbl_" + name
    return name[:60]


def _pg_type(dtype) -> str:
    kind = str(dtype)
    if "int" in kind:   return "BIGINT"
    if "float" in kind: return "DOUBLE PRECISION"
    if "bool" in kind:  return "BOOLEAN"
    if "datetime" in kind: return "TIMESTAMPTZ"
    if "date" in kind:  return "DATE"
    return "TEXT"


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how="all")
    df.columns = [_sanitise_name(str(c)) for c in df.columns]
    seen: dict[str, int] = {}
    new_cols = []
    for c in df.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df.columns = new_cols
    return df


def read_uploaded_file(uploaded_file) -> tuple[pd.DataFrame, str]:
    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv") or name.endswith(".txt"):
            raw = uploaded_file.read()
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=",", on_bad_lines="skip")
                if df.shape[1] == 1:
                    df = pd.read_csv(io.BytesIO(raw), sep="\t", on_bad_lines="skip")
            except Exception:
                df = pd.read_csv(io.BytesIO(raw), sep="\t", on_bad_lines="skip")
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(uploaded_file, engine="openpyxl" if name.endswith("xlsx") else "xlrd")
        else:
            return pd.DataFrame(), f"Unsupported file type: {uploaded_file.name}"

        if df.empty:
            return pd.DataFrame(), "The file appears to be empty."

        df = _clean_df(df)
        return df, ""
    except Exception as e:
        return pd.DataFrame(), f"Could not read file: {str(e)}"


def import_dataframe_to_db(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> tuple[bool, str]:
    table_name = _sanitise_name(table_name)
    col_defs = ",\n    ".join(f'"{col}" {_pg_type(df[col].dtype)}' for col in df.columns)
    create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    {col_defs}\n);'
    drop_sql   = f'DROP TABLE IF EXISTS "{table_name}";'
    placeholders = ", ".join(["%s"] * len(df.columns))
    col_names    = ", ".join(f'"{c}"' for c in df.columns)
    insert_sql   = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
    rows = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False, name=None)]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if if_exists == "replace":
                    cur.execute(drop_sql)
                cur.execute(create_sql)
                psycopg2.extras.execute_batch(cur, insert_sql, rows, page_size=500)
        return True, f"✅ Imported {len(rows):,} rows into table `{table_name}`."
    except Exception as e:
        return False, f"Import failed: {str(e)}"