"""Data profiling and a simple data quality score."""
import pandas as pd


def profile(df: pd.DataFrame) -> dict:
    rows = len(df)
    columns = {}
    for col in df.columns:
        s = df[col]
        info = {
            "dtype": str(s.dtype),
            "null_pct": round(float(s.isna().mean() * 100), 2) if rows else 0.0,
            "unique": int(s.nunique(dropna=True)),
            "sample": [str(v) for v in s.dropna().head(3).tolist()],
        }
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            info.update(min=float(s.min()), max=float(s.max()), mean=round(float(s.mean()), 3))
        columns[str(col)] = info

    duplicates = int(df.duplicated().sum())
    return {
        "rows": rows,
        "columns": columns,
        "duplicate_rows": duplicates,
        "quality_score": quality_score(df),
    }


def quality_score(df: pd.DataFrame) -> float:
    """100 minus average null % minus duplicate %. Simple but useful."""
    if len(df) == 0 or df.shape[1] == 0:
        return 0.0
    null_pct = df.isna().mean().mean() * 100
    dup_pct = df.duplicated().mean() * 100
    return round(max(0.0, 100 - null_pct - dup_pct), 2)
