-- Generated from local MCP registry.
-- Replace PROJECT_ID and DATASET_ID before running.

MERGE `PROJECT_ID.DATASET_ID.companies` target
USING (

  SELECT
    'saldao-center' AS company_id,
    'Saldao Center' AS company_name,
    'active' AS status,
    CAST(NULL AS STRING) AS segment,
    '5513997258292' AS whatsapp,
    CAST(NULL AS STRING) AS meta_ad_account_id,
    CAST(NULL AS STRING) AS meta_pixel_id,
    CAST(NULL AS STRING) AS facebook_page_id,
    CAST(NULL AS STRING) AS instagram_account_id,
    'Multigrow' AS crm_name,
    'Tiny ERP / Olist' AS erp_name,
    '1SIrBdhLKB9TROzjciUkcyhUk9A4avaAtcUKE9IN3rYE' AS google_sheet_id,
    CAST(NULL AS STRING) AS ga4_property_id,
    CAST(NULL AS STRING) AS gtm_container_id,
    CURRENT_TIMESTAMP() AS created_at,
    CURRENT_TIMESTAMP() AS updated_at
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
    STRUCT('saldao-center' AS company_id, 'composio' AS source_key, 'Composio' AS source_name, 'connector' AS source_type, 'configured' AS status, CAST(NULL AS STRING) AS connection_ref, 'daily' AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, 'Usado como caminho protegido para contas online.' AS notes, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('saldao-center' AS company_id, 'google_sheets' AS source_key, 'Google Sheets' AS source_name, 'connector' AS source_type, 'configured_apps_script' AS status, CAST(NULL AS STRING) AS connection_ref, 'daily' AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, 'Planilha Olist Vendas / Mes integrada por Apps Script.' AS notes, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('saldao-center' AS company_id, 'metaads' AS source_key, 'Metaads' AS source_name, 'connector' AS source_type, 'pending_config' AS status, CAST(NULL AS STRING) AS connection_ref, 'daily' AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, 'Conectar/confirmar conta Meta por empresa antes de executar acoes online.' AS notes, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('saldao-center' AS company_id, 'multigrow' AS source_key, 'Multigrow' AS source_name, 'connector' AS source_type, 'configured_webhook' AS status, CAST(NULL AS STRING) AS connection_ref, 'daily' AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, 'Webhook CRM ja foi usado para eventos locais.' AS notes, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('saldao-center' AS company_id, 'tiny' AS source_key, 'Tiny' AS source_name, 'connector' AS source_type, 'configured_local_env' AS status, CAST(NULL AS STRING) AS connection_ref, 'daily' AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, 'Token continua fora do banco, em variavel local/App Script.' AS notes, CURRENT_TIMESTAMP() AS updated_at)
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
