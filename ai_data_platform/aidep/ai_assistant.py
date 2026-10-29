"""AI layer.

Uses Claude (if ANTHROPIC_API_KEY is set) to:
  1. build a cleaning plan from a data profile
  2. turn natural-language questions into SQL

Both fall back to simple rule-based logic when no API key / network is available.
"""
import json
import re
import warnings

import pandas as pd

from . import config

VALID_TYPES = {"int", "float", "string", "date", "bool"}
VALID_FILLS = {"mean", "median", "mode", "zero", "unknown", "drop", "none"}


# ---------------------------------------------------------------- LLM helper
def _ask_claude(prompt: str, max_tokens: int = 1500) -> str | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as exc:  # network, auth, missing package...
        print(f"[ai] Claude call failed ({exc}); using rule-based fallback.")
        return None


def _extract_json(text: str) -> dict | None:
    try:
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except (ValueError, json.JSONDecodeError):
        return None


# -------------------------------------------------------------- cleaning plan
def build_cleaning_plan(profile: dict, df: pd.DataFrame) -> dict:
    prompt = f"""You are a data engineer. Given this dataset profile, return ONLY a JSON object:
{{
  "column_types": {{"<column>": "int|float|string|date|bool"}},
  "fill_strategy": {{"<column>": "mean|median|mode|zero|unknown|drop|none"}},
  "drop_columns": ["<column>"],
  "notes": ["short explanation of key decisions"]
}}
Use the exact column names. Drop columns only if mostly empty or useless.

Profile:
{json.dumps(profile, indent=2)}"""

    reply = _ask_claude(prompt)
    plan = _extract_json(reply) if reply else None
    if plan:
        plan = _validate_plan(plan, df)
        plan["source"] = "claude"
        return plan

    plan = _heuristic_plan(profile, df)
    plan["source"] = "rule-based"
    return plan


def _validate_plan(plan: dict, df: pd.DataFrame) -> dict:
    cols = set(df.columns)
    return {
        "column_types": {c: t for c, t in plan.get("column_types", {}).items()
                         if c in cols and t in VALID_TYPES},
        "fill_strategy": {c: f for c, f in plan.get("fill_strategy", {}).items()
                          if c in cols and f in VALID_FILLS},
        "drop_columns": [c for c in plan.get("drop_columns", []) if c in cols],
        "notes": [str(n) for n in plan.get("notes", [])],
    }


def _heuristic_plan(profile: dict, df: pd.DataFrame) -> dict:
    types, fills, drops, notes = {}, {}, [], []
    for col, info in profile["columns"].items():
        s = df[col]
        if info["null_pct"] > 60:
            drops.append(col)
            notes.append(f"Dropped '{col}' ({info['null_pct']}% empty).")
            continue

        if pd.api.types.is_bool_dtype(s):
            types[col], fills[col] = "bool", "none"
        elif pd.api.types.is_integer_dtype(s):
            types[col], fills[col] = "int", "median"
        elif pd.api.types.is_float_dtype(s):
            types[col], fills[col] = "float", "median"
        else:
            if _looks_like_date(s):
                types[col], fills[col] = "date", "none"
                notes.append(f"Detected '{col}' as a date column.")
            elif _looks_numeric(s):
                types[col], fills[col] = "float", "median"
                notes.append(f"Converted '{col}' from text to number.")
            else:
                types[col], fills[col] = "string", "unknown"
    return {"column_types": types, "fill_strategy": fills, "drop_columns": drops, "notes": notes}


def _looks_like_date(s: pd.Series) -> bool:
    sample = s.dropna().astype(str).head(50)
    if sample.empty:
        return False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        parsed = pd.to_datetime(sample, errors="coerce")
    return parsed.notna().mean() >= 0.8 and sample.str.contains(r"[-/]").mean() > 0.8


def _looks_numeric(s: pd.Series) -> bool:
    sample = s.dropna().astype(str).head(50)
    if sample.empty:
        return False
    cleaned = sample.str.replace(r"[$,₹€\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce").notna().mean() >= 0.8


# ------------------------------------------------------------ text-to-SQL
def question_to_sql(question: str, schema: dict) -> str | None:
    prompt = f"""Write ONE read-only SQLite SELECT query that answers the question.
Return only the SQL, no explanation, no markdown.

Schema (table -> columns):
{json.dumps(schema, indent=2)}

Question: {question}"""
    reply = _ask_claude(prompt, max_tokens=400)
    if not reply:
        return None
    sql = re.sub(r"^```(?:sql)?|```$", "", reply.strip(), flags=re.MULTILINE).strip()
    return sql
