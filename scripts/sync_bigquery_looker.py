# -*- coding: utf-8 -*-
"""
Sync local MCP data into BigQuery tables used by Looker Studio.

This script sends:
- companies
- company data sources
- MCP audit logs
- Meta campaign snapshots when company meta_ad_account_id is configured
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from decimal import Decimal
import json
import sys
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from google.cloud import bigquery

from src.audit_log import list_audit_logs
from src.bigquery_config import get_bigquery_config
from src.company_store import list_companies, list_company_connections
from src.meta_online import MetaOnlineError, listar_campanhas_meta


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def table_id(config, table_name: str) -> str:
    return f"{config.project_id}.{config.dataset_id}.{table_name}"


def clean_dict(row: dict[str, Any]) -> dict[str, Any]:
    clean = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            clean[key] = float(value)
        elif isinstance(value, (datetime, date)):
            clean[key] = value.isoformat()
        else:
            clean[key] = value
    return clean


def insert_rows(client: bigquery.Client, table: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        print(f"Sem linhas para {table}")
        return
    errors = client.insert_rows_json(table, [clean_dict(row) for row in rows])
    if errors:
        raise RuntimeError(f"Erro ao inserir em {table}: {errors}")
    print(f"{len(rows)} linhas inseridas em {table}")


def sync_companies(client: bigquery.Client, config) -> None:
    now = utc_now()
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
                "created_at": company.get("created_at") or now,
                "updated_at": company.get("updated_at") or now,
            }
        )
    insert_rows(client, table_id(config, "companies"), rows)


def sync_data_sources(client: bigquery.Client, config) -> None:
    rows = []
    for company in list_companies(include_inactive=True):
        for connection in list_company_connections(company["company_id"]):
            service = connection["service"]
            rows.append(
                {
                    "company_id": connection["company_id"],
                    "source_key": service,
                    "source_name": service.replace("_", " ").title(),
                    "source_type": "connector",
                    "status": connection["status"],
                    "connection_ref": connection.get("external_account_id") or "",
                    "refresh_frequency": "daily",
                    "last_sync_at": None,
                    "notes": connection.get("notes") or "",
                    "updated_at": connection.get("updated_at") or utc_now(),
                }
            )
    insert_rows(client, table_id(config, "company_data_sources"), rows)


def sync_audit_logs(client: bigquery.Client, config, limit: int = 500) -> None:
    rows = []
    for item in list_audit_logs(limit=limit):
        rows.append(
            {
                "id": str(item["id"]),
                "ts": item["ts"],
                "company_id": item.get("company_id"),
                "actor": item.get("actor") or "local-user",
                "tool": item.get("tool") or "",
                "action": item.get("action") or "",
                "target": item.get("target"),
                "status": item.get("status") or "",
                "message": item.get("message") or "",
                "metadata_json": json.dumps(item.get("metadata") or {}, ensure_ascii=False),
            }
        )
    insert_rows(client, table_id(config, "mcp_audit_logs"), rows)


def parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_numeric(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sync_meta_campaigns(client: bigquery.Client, config) -> None:
    rows = []
    today = date.today().isoformat()
    for company in list_companies(include_inactive=False):
        ad_account_id = company.get("meta_ad_account_id")
        if not ad_account_id:
            print(f"Pulando Meta Ads de {company['company_id']}: meta_ad_account_id ausente")
            continue
        try:
            result = listar_campanhas_meta(ad_account_id, limite=100)
        except MetaOnlineError as exc:
            print(f"Meta Ads nao sincronizado para {company['company_id']}: {exc}")
            continue
        campaigns = result.get("resultado", {}).get("data") if isinstance(result.get("resultado"), dict) else result.get("resultado", [])
        if not campaigns:
            continue
        for campaign in campaigns:
            rows.append(
                {
                    "company_id": company["company_id"],
                    "date": today,
                    "ad_account_id": ad_account_id,
                    "campaign_id": campaign.get("id"),
                    "campaign_name": campaign.get("name"),
                    "campaign_status": campaign.get("effective_status") or campaign.get("status"),
                    "objective": campaign.get("objective"),
                    "spend": None,
                    "impressions": None,
                    "reach": None,
                    "clicks": None,
                    "inline_link_clicks": None,
                    "leads": None,
                    "purchases": None,
                    "purchase_value": None,
                    "ctr": parse_numeric(campaign.get("ctr")),
                    "cpc": parse_numeric(campaign.get("cpc")),
                    "cpm": parse_numeric(campaign.get("cpm")),
                    "cost_per_lead": None,
                    "roas": None,
                    "updated_at": utc_now(),
                }
            )
    insert_rows(client, table_id(config, "meta_campaign_daily"), rows)


def main() -> None:
    config = get_bigquery_config()
    client = bigquery.Client(project=config.project_id)
    sync_companies(client, config)
    sync_data_sources(client, config)
    sync_audit_logs(client, config)
    sync_meta_campaigns(client, config)


if __name__ == "__main__":
    main()

