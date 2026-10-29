"""Storage layer: SQLite 'warehouse' + pipeline run log."""
import sqlite3
from datetime import datetime

import pandas as pd

from . import config


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(config.DB_PATH)


def save_table(df: pd.DataFrame, table: str) -> None:
    with _conn() as con:
        df.to_sql(table, con, if_exists="replace", index=False)


def log_run(source: str, table: str, rows_in: int, rows_out: int,
            score_before: float, score_after: float, plan_source: str) -> None:
    with _conn() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS pipeline_runs (
                run_at TEXT, source TEXT, table_name TEXT, rows_in INTEGER,
                rows_out INTEGER, quality_before REAL, quality_after REAL, plan_source TEXT)"""
        )
        con.execute(
            "INSERT INTO pipeline_runs VALUES (?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), source, table,
             rows_in, rows_out, score_before, score_after, plan_source),
        )


def get_schema() -> dict:
    with _conn() as con:
        tables = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'pipeline_runs'")]
        return {t: [r[1] for r in con.execute(f'PRAGMA table_info("{t}")')] for t in tables}


def run_query(sql: str) -> pd.DataFrame:
    if not sql.strip().lower().startswith(("select", "with")):
        raise ValueError("Only read-only SELECT queries are allowed.")
    with _conn() as con:
        return pd.read_sql_query(sql, con)
