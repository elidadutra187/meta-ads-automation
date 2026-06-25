# -*- coding: utf-8 -*-
"""
BigQuery/Looker Studio configuration helpers.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class BigQueryConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class BigQueryConfig:
    project_id: str
    dataset_id: str

    @property
    def dataset_ref(self) -> str:
        return f"{self.project_id}.{self.dataset_id}"


def _validate_identifier(name: str, value: str, pattern: str) -> str:
    value = (value or "").strip()
    if not value or value.startswith("seu-"):
        raise BigQueryConfigError(f"Configure {name} no .env.")
    if not re.fullmatch(pattern, value):
        raise BigQueryConfigError(f"{name} invalido: {value}")
    return value


def get_bigquery_config() -> BigQueryConfig:
    project_id = _validate_identifier(
        "BIGQUERY_PROJECT_ID",
        os.getenv("BIGQUERY_PROJECT_ID", ""),
        r"[a-z][a-z0-9-]{4,28}[a-z0-9]",
    )
    dataset_id = _validate_identifier(
        "BIGQUERY_DATASET_ID",
        os.getenv("BIGQUERY_DATASET_ID", "mcp_marketing_ops"),
        r"[A-Za-z_][A-Za-z0-9_]{0,1023}",
    )
    return BigQueryConfig(project_id=project_id, dataset_id=dataset_id)

