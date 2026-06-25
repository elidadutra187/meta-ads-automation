# -*- coding: utf-8 -*-
"""
Generate BigQuery MERGE SQL from the local MCP company registry.
"""
from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.company_store import list_companies, list_company_connections

OUT_PATH = BASE_DIR / "looker_studio" / "empresas_conectadas_merge.sql"


def sql_string(value: object) -> str:
    if value is None or value == "":
        return "CAST(NULL AS STRING)"
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def company_select(company: dict) -> str:
    return f"""
  SELECT
    {sql_string(company['company_id'])} AS company_id,
    {sql_string(company['name'])} AS company_name,
    {sql_string(company['status'])} AS status,
    CAST(NULL AS STRING) AS segment,
    {sql_string(company.get('whatsapp'))} AS whatsapp,
    {sql_string(company.get('meta_ad_account_id'))} AS meta_ad_account_id,
    {sql_string(company.get('meta_pixel_id'))} AS meta_pixel_id,
    {sql_string(company.get('facebook_page_id'))} AS facebook_page_id,
    {sql_string(company.get('instagram_account_id'))} AS instagram_account_id,
    {sql_string(company.get('crm_name'))} AS crm_name,
    {sql_string(company.get('erp_name'))} AS erp_name,
    {sql_string(company.get('google_sheet_id'))} AS google_sheet_id,
    {sql_string(company.get('ga4_property_id'))} AS ga4_property_id,
    {sql_string(company.get('gtm_container_id'))} AS gtm_container_id,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at"""


def connection_struct(connection: dict) -> str:
    return (
        "    STRUCT("
        f"{sql_string(connection['company_id'])} AS company_id, "
        f"{sql_string(connection['service'])} AS source_key, "
        f"{sql_string(connection['service'].replace('_', ' ').title())} AS source_name, "
        "'connector' AS source_type, "
        f"{sql_string(connection['status'])} AS status, "
        f"{sql_string(connection.get('external_account_id'))} AS connection_ref, "
        "'daily' AS refresh_frequency, "
        "CAST(NULL AS TIMESTAMP) AS last_sync_at, "
        f"{sql_string(connection.get('notes'))} AS notes, "
        "CURRENT_TIMESTAMP() AS updated_at)"
    )


def build_sql() -> str:
    companies = list_companies(include_inactive=True)
    selects = "\n  UNION ALL".join(company_select(company) for company in companies)
    connections = []
    for company in companies:
        connections.extend(list_company_connections(company["company_id"]))

    structs = ",\n".join(connection_struct(connection) for connection in connections)
    if not structs:
        structs = (
            "    STRUCT(CAST(NULL AS STRING) AS company_id, CAST(NULL AS STRING) AS source_key, "
            "CAST(NULL AS STRING) AS source_name, CAST(NULL AS STRING) AS source_type, "
            "CAST(NULL AS STRING) AS status, CAST(NULL AS STRING) AS connection_ref, "
            "CAST(NULL AS STRING) AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, "
            "CAST(NULL AS STRING) AS notes, CURRENT_TIMESTAMP() AS updated_at)"
        )

    return f"""-- Generated from local MCP registry.
-- Replace PROJECT_ID and DATASET_ID before running.

MERGE `PROJECT_ID.DATASET_ID.companies` target
USING (
{selects}
) source
ON target.company_id = source.company_id
WHEN MATCHED THEN UPDATE SET
  company_name = source.company_name,
  status = source.status,
  whatsapp = source.whatsapp,
  meta_ad_account_id = source.meta_ad_account_id,
  meta_pixel_id = source.meta_pixel_id,
  facebook_page_id = source.facebook_page_id,
  instagram_account_id = source.instagram_account_id,
  crm_name = source.crm_name,
  erp_name = source.erp_name,
  google_sheet_id = source.google_sheet_id,
  ga4_property_id = source.ga4_property_id,
  gtm_container_id = source.gtm_container_id,
  updated_at = source.updated_at
WHEN NOT MATCHED THEN INSERT (
  company_id, company_name, status, segment, whatsapp, meta_ad_account_id,
  meta_pixel_id, facebook_page_id, instagram_account_id, crm_name, erp_name,
  google_sheet_id, ga4_property_id, gtm_container_id, created_at, updated_at
) VALUES (
  source.company_id, source.company_name, source.status, source.segment,
  source.whatsapp, source.meta_ad_account_id, source.meta_pixel_id,
  source.facebook_page_id, source.instagram_account_id, source.crm_name,
  source.erp_name, source.google_sheet_id, source.ga4_property_id,
  source.gtm_container_id, source.created_at, source.updated_at
);

MERGE `PROJECT_ID.DATASET_ID.company_data_sources` target
USING (
  SELECT * FROM UNNEST([
{structs}
  ])
) source
ON target.company_id = source.company_id
AND target.source_key = source.source_key
WHEN MATCHED THEN UPDATE SET
  source_name = source.source_name,
  source_type = source.source_type,
  status = source.status,
  connection_ref = source.connection_ref,
  refresh_frequency = source.refresh_frequency,
  last_sync_at = source.last_sync_at,
  notes = source.notes,
  updated_at = source.updated_at
WHEN NOT MATCHED THEN INSERT (
  company_id, source_key, source_name, source_type, status, connection_ref,
  refresh_frequency, last_sync_at, notes, updated_at
) VALUES (
  source.company_id, source.source_key, source.source_name, source.source_type,
  source.status, source.connection_ref, source.refresh_frequency,
  source.last_sync_at, source.notes, source.updated_at
);
"""


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(build_sql(), encoding="utf-8")
    print(f"SQL gerado em: {OUT_PATH}")


if __name__ == "__main__":
    main()
