# -*- coding: utf-8 -*-
"""
Export local MCP registry rows as JSONL files for bq load.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.audit_log import list_audit_logs
from src.company_store import list_companies, list_company_connections

OUT_DIR = BASE_DIR / "data" / "bigquery_load"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"{len(rows)} linhas em {path}")


def export_companies() -> list[dict]:
    rows = []
    for company in list_companies(include_inactive=True):
        rows.append(
            {
                "company_id": company["company_id"],
                "company_name": company["name"],
                "status": company["status"],
                "segment": None,
                "whatsapp": company.get("whatsapp"),
                "meta_ad_account_id": company.get("meta_ad_account_id"),
                "meta_pixel_id": company.get("meta_pixel_id"),
                "facebook_page_id": company.get("facebook_page_id"),
                "instagram_account_id": company.get("instagram_account_id"),
                "crm_name": company.get("crm_name"),
                "erp_name": company.get("erp_name"),
                "google_sheet_id": company.get("google_sheet_id"),
                "ga4_property_id": company.get("ga4_property_id"),
                "gtm_container_id": company.get("gtm_container_id"),
                "created_at": company.get("created_at"),
                "updated_at": company.get("updated_at"),
            }
        )
    return rows


def export_data_sources() -> list[dict]:
    rows = []
    for company in list_companies(include_inactive=True):
        for source in list_company_connections(company["company_id"]):
            service = source["service"]
            rows.append(
                {
                    "company_id": source["company_id"],
                    "source_key": service,
                    "source_name": service.replace("_", " ").title(),
                    "source_type": "connector",
                    "status": source["status"],
                    "connection_ref": source.get("external_account_id") or "",
                    "refresh_frequency": "daily",
                    "last_sync_at": None,
                    "notes": source.get("notes") or "",
                    "updated_at": source.get("updated_at"),
                }
            )
    return rows


def export_audit_logs() -> list[dict]:
    rows = []
    for audit in list_audit_logs(limit=500):
        rows.append(
            {
                "id": str(audit["id"]),
                "ts": audit["ts"],
                "company_id": audit.get("company_id"),
                "actor": audit.get("actor") or "local-user",
                "tool": audit.get("tool") or "",
                "action": audit.get("action") or "",
                "target": audit.get("target"),
                "status": audit.get("status") or "",
                "message": audit.get("message") or "",
                "metadata_json": json.dumps(audit.get("metadata") or {}, ensure_ascii=False),
            }
        )
    return rows


def main() -> None:
    write_jsonl(OUT_DIR / "companies.jsonl", export_companies())
    write_jsonl(OUT_DIR / "company_data_sources.jsonl", export_data_sources())
    write_jsonl(OUT_DIR / "mcp_audit_logs.jsonl", export_audit_logs())


if __name__ == "__main__":
    main()

