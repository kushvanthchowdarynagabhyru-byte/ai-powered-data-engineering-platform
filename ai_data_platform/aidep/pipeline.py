"""Orchestrates: ingest -> profile -> AI plan -> transform -> validate -> store."""
from pathlib import Path

from . import ai_assistant, ingest, profiler, storage, transform
from .profiler import quality_score


def run_pipeline(path: str, table: str | None = None) -> dict:
    table = table or transform.to_snake(Path(path).stem)

    print(f"[1/6] Ingesting {path}")
    raw = ingest.load_file(path)

    print("[2/6] Profiling raw data")
    prof = profiler.profile(raw)
    print(f"      {prof['rows']} rows, {len(prof['columns'])} columns, "
          f"{prof['duplicate_rows']} duplicates, quality {prof['quality_score']}")

    print("[3/6] Building cleaning plan")
    plan = ai_assistant.build_cleaning_plan(prof, raw)
    print(f"      plan source: {plan['source']}")
    for note in plan.get("notes", []):
        print(f"      - {note}")

    print("[4/6] Transforming data")
    clean, log = transform.apply_plan(raw, plan)
    for line in log:
        print(f"      - {line}")

    print("[5/6] Validating")
    after = quality_score(clean)
    print(f"      quality score: {prof['quality_score']} -> {after}")

    print(f"[6/6] Loading into warehouse table '{table}'")
    storage.save_table(clean, table)
    storage.log_run(path, table, len(raw), len(clean),
                    prof["quality_score"], after, plan["source"])

    return {"table": table, "rows_in": len(raw), "rows_out": len(clean),
            "quality_before": prof["quality_score"], "quality_after": after}
