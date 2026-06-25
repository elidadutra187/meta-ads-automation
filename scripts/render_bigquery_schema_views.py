# -*- coding: utf-8 -*-
"""
Render only BigQuery schema and Looker views, skipping MERGE/DML.

Use this when the Google Cloud project has no billing enabled. BigQuery free
sandbox blocks DML, but schema creation and load jobs can still be used.
"""
from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.bigquery_config import get_bigquery_config

TEMPLATE_PATH = BASE_DIR / "looker_studio" / "bigquery_multiempresa.sql"
OUT_PATH = BASE_DIR / "looker_studio" / "bigquery_schema_views_rendered.sql"


def strip_dml(sql: str, config) -> str:
    companies_merge = f"MERGE `{config.project_id}.{config.dataset_id}.companies`"
    first_view = f"CREATE OR REPLACE VIEW `{config.project_id}.{config.dataset_id}.vw_looker_company_pages`"
    first_merge_index = sql.index(companies_merge)
    first_view_index = sql.index(first_view)
    return sql[:first_merge_index] + sql[first_view_index:]


def main() -> None:
    config = get_bigquery_config()
    sql = TEMPLATE_PATH.read_text(encoding="utf-8")
    sql = sql.replace("PROJECT_ID", config.project_id)
    sql = sql.replace("DATASET_ID", config.dataset_id)
    OUT_PATH.write_text(strip_dml(sql, config), encoding="utf-8")
    print(f"SQL sem DML renderizado em: {OUT_PATH}")
    print(f"Dataset: {config.dataset_ref}")


if __name__ == "__main__":
    main()

