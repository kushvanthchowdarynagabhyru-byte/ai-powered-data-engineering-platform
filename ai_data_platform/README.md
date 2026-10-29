# AI-Powered Data Engineering Platform (base project)

A small end-to-end data pipeline where an AI model helps decide how to clean the data.

```
file (csv/json/xlsx) -> ingest -> profile -> AI cleaning plan -> transform -> validate -> SQLite warehouse
                                                                                          |
                                                                       SQL queries / plain-English questions
```

## Structure
```
main.py                  CLI entry point
generate_sample_data.py  creates a messy demo CSV
aidep/
  config.py              paths, model name, API key
  ingest.py              load csv/json/excel
  profiler.py            column stats + data quality score
  ai_assistant.py        Claude-powered cleaning plan + text-to-SQL (with rule-based fallback)
  transform.py           applies the plan (dedupe, types, fill nulls, snake_case)
  storage.py             SQLite warehouse + run log
  pipeline.py            orchestrates all steps
```

## Quick start
```bash
pip install -r requirements.txt
python generate_sample_data.py
python main.py run data/sample_sales.csv
python main.py tables
python main.py query "SELECT region, SUM(total) AS revenue FROM sample_sales GROUP BY region"
```

## Enable the AI features
```bash
export ANTHROPIC_API_KEY=your_key
python main.py run data/sample_sales.csv       # Claude builds the cleaning plan
python main.py ask "Which product sold the most units?"
```
Without a key, the pipeline still works using rule-based logic.

## Ideas to extend
- Schedule runs with Airflow / cron
- Add Parquet output or a Postgres/BigQuery loader
- Add a Streamlit dashboard
- Anomaly detection and schema-drift alerts
