"""Apply a cleaning plan to a DataFrame."""
import re
import warnings

import pandas as pd


def to_snake(name: str) -> str:
    name = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip())
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    return name.strip("_").lower()


def apply_plan(df: pd.DataFrame, plan: dict) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    log: list[str] = []

    before = len(df)
    df = df.drop_duplicates()
    if len(df) < before:
        log.append(f"Removed {before - len(df)} duplicate rows.")

    drops = [c for c in plan.get("drop_columns", []) if c in df.columns]
    if drops:
        df = df.drop(columns=drops)
        log.append(f"Dropped columns: {drops}")

    # trim whitespace in text columns
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()

    types = plan.get("column_types", {})
    fills = plan.get("fill_strategy", {})

    for col in list(df.columns):
        t, how = types.get(col), fills.get(col, "none")

        # 1) type casting
        if t in ("int", "float"):
            if df[col].dtype == object or str(df[col].dtype) == "string":
                df[col] = df[col].astype("string").str.replace(r"[$,₹€\s]", "", regex=True)
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif t == "date":
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df[col] = pd.to_datetime(df[col], errors="coerce")
        elif t == "string":
            df[col] = df[col].astype("string")

        # 2) missing values
        n_null = int(df[col].isna().sum())
        if n_null and how != "none":
            if how == "drop":
                df = df.dropna(subset=[col])
            elif how in ("mean", "median") and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(getattr(df[col], how)())
            elif how == "mode" and not df[col].mode().empty:
                df[col] = df[col].fillna(df[col].mode().iloc[0])
            elif how == "zero" and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(0)
            elif how == "unknown":
                df[col] = df[col].astype("string").fillna("Unknown")
            log.append(f"Filled {n_null} missing values in '{col}' using {how}.")

        # 3) final integer cast (after fill)
        if t == "int" and pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].round().astype("Int64")

        # 4) normalise low-cardinality text (e.g. 'north', 'NORTH ' -> 'North')
        if t == "string" and df[col].nunique() <= 20:
            df[col] = df[col].str.title()

    df.columns = [to_snake(c) for c in df.columns]
    log.append("Renamed columns to snake_case.")
    return df.reset_index(drop=True), log
