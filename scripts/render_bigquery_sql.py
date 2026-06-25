# -*- coding: utf-8 -*-
"""
Render Looker Studio BigQuery SQL replacing PROJECT_ID and DATASET_ID.
"""
from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.bigquery_config import get_bigquery_config

TEMPLATE_PATH = BASE_DIR / "looker_studio" / "bigquery_multiempresa.sql"
OUT_PATH = BASE_DIR / "looker_studio" / "bigquery_multiempresa_rendered.sql"


def main() -> None:
    config = get_bigquery_config()
    sql = TEMPLATE_PATH.read_text(encoding="utf-8")
    sql = sql.replace("PROJECT_ID", config.project_id)
    sql = sql.replace("DATASET_ID", config.dataset_id)
    OUT_PATH.write_text(sql, encoding="utf-8")
    print(f"SQL renderizado em: {OUT_PATH}")
    print(f"Dataset: {config.dataset_ref}")


if __name__ == "__main__":
    main()

