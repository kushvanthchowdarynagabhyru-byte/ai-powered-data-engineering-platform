"""CLI for the AI-Powered Data Engineering Platform.

Usage:
  python main.py run data/sample_sales.csv
  python main.py query "SELECT region, SUM(total) FROM sample_sales GROUP BY region"
  python main.py ask "Which region has the highest total sales?"
  python main.py tables
"""
import argparse

import pandas as pd

from aidep import ai_assistant, pipeline, storage

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 30)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-Powered Data Engineering Platform")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run the pipeline on a file")
    p_run.add_argument("path")
    p_run.add_argument("--table", help="target table name")

    p_q = sub.add_parser("query", help="run a SQL SELECT")
    p_q.add_argument("sql")

    p_ask = sub.add_parser("ask", help="ask a question in plain English (needs ANTHROPIC_API_KEY)")
    p_ask.add_argument("question")

    sub.add_parser("tables", help="list warehouse tables")

    args = parser.parse_args()

    if args.cmd == "run":
        result = pipeline.run_pipeline(args.path, args.table)
        print("\nDone:", result)
    elif args.cmd == "query":
        print(storage.run_query(args.sql).to_string(index=False))
    elif args.cmd == "ask":
        sql = ai_assistant.question_to_sql(args.question, storage.get_schema())
        if not sql:
            print("Natural-language queries need ANTHROPIC_API_KEY. Use the 'query' command instead.")
            return
        print(f"SQL: {sql}\n")
        print(storage.run_query(sql).to_string(index=False))
    elif args.cmd == "tables":
        for table, cols in storage.get_schema().items():
            print(f"{table}: {', '.join(cols)}")


if __name__ == "__main__":
    main()
