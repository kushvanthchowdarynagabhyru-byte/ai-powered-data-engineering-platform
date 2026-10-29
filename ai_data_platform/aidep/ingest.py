"""Ingestion layer: load CSV / JSON / Excel files into a DataFrame."""
from pathlib import Path

import pandas as pd


def load_file(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = p.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(p)
    if ext == ".json":
        return pd.read_json(p)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(p)
    raise ValueError(f"Unsupported file type: {ext} (use csv, json, xlsx)")
