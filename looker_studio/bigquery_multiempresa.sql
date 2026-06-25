-- BigQuery Standard SQL
-- Replace PROJECT_ID and DATASET_ID before running.
--
-- Goal:
-- - one row per connected company
-- - one data-source registry per company
-- - Looker Studio-ready views for one report page per company
--
-- Recommended dataset name: mcp_marketing_ops

CREATE SCHEMA IF NOT EXISTS `PROJECT_ID.DATASET_ID`;

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.companies` (
  company_id STRING NOT NULL,
  company_name STRING NOT NULL,
  status STRING NOT NULL,
  segment STRING,
  whatsapp STRING,
  meta_ad_account_id STRING,
  meta_pixel_id STRING,
  facebook_page_id STRING,
  instagram_account_id STRING,
  crm_name STRING,
  erp_name STRING,
  google_sheet_id STRING,
  ga4_property_id STRING,
  gtm_container_id STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.company_data_sources` (
  company_id STRING NOT NULL,
  source_key STRING NOT NULL,
  source_name STRING NOT NULL,
  source_type STRING NOT NULL,
  status STRING NOT NULL,
  connection_ref STRING,
  refresh_frequency STRING,
  last_sync_at TIMESTAMP,
  notes STRING,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.meta_campaign_daily` (
  company_id STRING NOT NULL,
  date DATE NOT NULL,
  ad_account_id STRING,
  campaign_id STRING,
  campaign_name STRING,
  campaign_status STRING,
  objective STRING,
  spend NUMERIC,
  impressions INT64,
  reach INT64,
  clicks INT64,
  inline_link_clicks INT64,
  leads INT64,
  purchases INT64,
  purchase_value NUMERIC,
  ctr NUMERIC,
  cpc NUMERIC,
  cpm NUMERIC,
  cost_per_lead NUMERIC,
  roas NUMERIC,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.crm_leads_daily` (
  company_id STRING NOT NULL,
  date DATE NOT NULL,
  crm_name STRING,
  source STRING,
  campaign_id STRING,
  campaign_name STRING,
  leads_created INT64,
  leads_qualified INT64,
  opportunities INT64,
  won_deals INT64,
  lost_deals INT64,
  revenue NUMERIC,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.erp_orders_daily` (
  company_id STRING NOT NULL,
  date DATE NOT NULL,
  erp_name STRING,
  orders_total INT64,
  orders_cancelled INT64,
  orders_effective INT64,
  gross_revenue NUMERIC,
  cancelled_revenue NUMERIC,
  net_revenue NUMERIC,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.ga4_daily` (
  company_id STRING NOT NULL,
  date DATE NOT NULL,
  property_id STRING,
  sessions INT64,
  users INT64,
  new_users INT64,
  conversions INT64,
  purchase_revenue NUMERIC,
  whatsapp_clicks INT64,
  form_submits INT64,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `PROJECT_ID.DATASET_ID.mcp_audit_logs` (
  id STRING,
  ts TIMESTAMP,
  company_id STRING,
  actor STRING,
  tool STRING,
  action STRING,
  target STRING,
  status STRING,
  message STRING,
  metadata_json STRING
);

MERGE `PROJECT_ID.DATASET_ID.companies` target
USING (
  SELECT
    'saldao-center' AS company_id,
    'Saldao Center' AS company_name,
    'active' AS status,
    'pisos-e-acabamentos' AS segment,
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
  segment = source.segment,
  whatsapp = source.whatsapp,
  crm_name = source.crm_name,
  erp_name = source.erp_name,
  google_sheet_id = source.google_sheet_id,
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
    STRUCT('saldao-center' AS company_id, 'metaads' AS source_key, 'Meta Ads' AS source_name, 'ads' AS source_type, 'pending_config' AS status, '' AS connection_ref, 'daily' AS refresh_frequency, CAST(NULL AS TIMESTAMP) AS last_sync_at, 'Confirmar conta de anuncio por empresa antes de alterar campanhas.' AS notes, CURRENT_TIMESTAMP() AS updated_at),
    STRUCT('saldao-center', 'tiny', 'Tiny ERP / Olist', 'erp', 'configured_local_env', '', 'hourly', CAST(NULL AS TIMESTAMP), 'Pedidos e cancelamentos alimentam planilha e receita operacional.', CURRENT_TIMESTAMP()),
    STRUCT('saldao-center', 'multigrow', 'Multigrow CRM', 'crm', 'configured_webhook', '', 'near_real_time', CAST(NULL AS TIMESTAMP), 'Eventos do CRM alimentam leads e oportunidades.', CURRENT_TIMESTAMP()),
    STRUCT('saldao-center', 'google_sheets', 'Olist Vendas / Mes', 'spreadsheet', 'configured_apps_script', '1SIrBdhLKB9TROzjciUkcyhUk9A4avaAtcUKE9IN3rYE', 'hourly', CAST(NULL AS TIMESTAMP), 'Planilha operacional de vendas.', CURRENT_TIMESTAMP()),
    STRUCT('saldao-center', 'composio', 'Composio', 'connector', 'configured', '', 'on_demand', CAST(NULL AS TIMESTAMP), 'Conector protegido para contas online.', CURRENT_TIMESTAMP()),
    STRUCT('saldao-center', 'ga4', 'Google Analytics 4', 'analytics', 'pending_config', '', 'daily', CAST(NULL AS TIMESTAMP), 'Configurar property_id para metricas de site.', CURRENT_TIMESTAMP()),
    STRUCT('saldao-center', 'gtm', 'Google Tag Manager', 'tag_manager', 'pending_config', '', 'on_publish', CAST(NULL AS TIMESTAMP), 'Configurar container_id para eventos e conversoes.', CURRENT_TIMESTAMP())
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

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_looker_company_pages` AS
SELECT
  c.company_id,
  c.company_name,
  CONCAT('Empresa - ', c.company_name) AS looker_page_name,
  c.status,
  c.segment,
  c.whatsapp,
  COUNTIF(ds.status IN ('configured', 'configured_local_env', 'configured_webhook', 'configured_apps_script', 'active')) AS connected_sources,
  COUNT(ds.source_key) AS total_sources,
  STRING_AGG(CONCAT(ds.source_name, ': ', ds.status), ' | ' ORDER BY ds.source_name) AS source_status_summary,
  c.updated_at
FROM `PROJECT_ID.DATASET_ID.companies` c
LEFT JOIN `PROJECT_ID.DATASET_ID.company_data_sources` ds
  ON ds.company_id = c.company_id
GROUP BY
  c.company_id, c.company_name, c.status, c.segment, c.whatsapp, c.updated_at;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_looker_data_sources` AS
SELECT
  c.company_id,
  c.company_name,
  ds.source_key,
  ds.source_name,
  ds.source_type,
  ds.status,
  ds.connection_ref,
  ds.refresh_frequency,
  ds.last_sync_at,
  ds.notes,
  ds.updated_at
FROM `PROJECT_ID.DATASET_ID.company_data_sources` ds
JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = ds.company_id;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_page_company_overview_daily` AS
WITH dates AS (
  SELECT company_id, date FROM `PROJECT_ID.DATASET_ID.meta_campaign_daily`
  UNION DISTINCT SELECT company_id, date FROM `PROJECT_ID.DATASET_ID.crm_leads_daily`
  UNION DISTINCT SELECT company_id, date FROM `PROJECT_ID.DATASET_ID.erp_orders_daily`
  UNION DISTINCT SELECT company_id, date FROM `PROJECT_ID.DATASET_ID.ga4_daily`
),
meta AS (
  SELECT
    company_id,
    date,
    SUM(spend) AS meta_spend,
    SUM(impressions) AS impressions,
    SUM(clicks) AS clicks,
    SUM(leads) AS meta_leads,
    SUM(purchase_value) AS meta_purchase_value
  FROM `PROJECT_ID.DATASET_ID.meta_campaign_daily`
  GROUP BY company_id, date
),
crm AS (
  SELECT
    company_id,
    date,
    SUM(leads_created) AS crm_leads,
    SUM(leads_qualified) AS qualified_leads,
    SUM(opportunities) AS opportunities,
    SUM(won_deals) AS won_deals,
    SUM(revenue) AS crm_revenue
  FROM `PROJECT_ID.DATASET_ID.crm_leads_daily`
  GROUP BY company_id, date
),
erp AS (
  SELECT
    company_id,
    date,
    SUM(orders_total) AS orders_total,
    SUM(orders_cancelled) AS orders_cancelled,
    SUM(orders_effective) AS orders_effective,
    SUM(gross_revenue) AS gross_revenue,
    SUM(cancelled_revenue) AS cancelled_revenue,
    SUM(net_revenue) AS net_revenue
  FROM `PROJECT_ID.DATASET_ID.erp_orders_daily`
  GROUP BY company_id, date
),
ga4 AS (
  SELECT
    company_id,
    date,
    SUM(sessions) AS sessions,
    SUM(users) AS users,
    SUM(conversions) AS ga4_conversions,
    SUM(whatsapp_clicks) AS whatsapp_clicks,
    SUM(form_submits) AS form_submits
  FROM `PROJECT_ID.DATASET_ID.ga4_daily`
  GROUP BY company_id, date
)
SELECT
  c.company_id,
  c.company_name,
  d.date,
  COALESCE(meta.meta_spend, 0) AS meta_spend,
  COALESCE(meta.impressions, 0) AS impressions,
  COALESCE(meta.clicks, 0) AS clicks,
  COALESCE(meta.meta_leads, 0) AS meta_leads,
  COALESCE(crm.crm_leads, 0) AS crm_leads,
  COALESCE(crm.qualified_leads, 0) AS qualified_leads,
  COALESCE(crm.opportunities, 0) AS opportunities,
  COALESCE(crm.won_deals, 0) AS won_deals,
  COALESCE(erp.orders_total, 0) AS orders_total,
  COALESCE(erp.orders_cancelled, 0) AS orders_cancelled,
  COALESCE(erp.orders_effective, 0) AS orders_effective,
  COALESCE(erp.gross_revenue, 0) AS gross_revenue,
  COALESCE(erp.cancelled_revenue, 0) AS cancelled_revenue,
  COALESCE(erp.net_revenue, 0) AS net_revenue,
  COALESCE(ga4.sessions, 0) AS sessions,
  COALESCE(ga4.users, 0) AS users,
  COALESCE(ga4.ga4_conversions, 0) AS ga4_conversions,
  COALESCE(ga4.whatsapp_clicks, 0) AS whatsapp_clicks,
  COALESCE(ga4.form_submits, 0) AS form_submits,
  SAFE_DIVIDE(COALESCE(meta.meta_spend, 0), NULLIF(COALESCE(crm.crm_leads, meta.meta_leads, 0), 0)) AS cost_per_lead,
  SAFE_DIVIDE(COALESCE(erp.net_revenue, crm.crm_revenue, meta.meta_purchase_value, 0), NULLIF(COALESCE(meta.meta_spend, 0), 0)) AS roas
FROM dates d
JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = d.company_id
LEFT JOIN meta
  ON meta.company_id = d.company_id AND meta.date = d.date
LEFT JOIN crm
  ON crm.company_id = d.company_id AND crm.date = d.date
LEFT JOIN erp
  ON erp.company_id = d.company_id AND erp.date = d.date
LEFT JOIN ga4
  ON ga4.company_id = d.company_id AND ga4.date = d.date;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_page_meta_ads` AS
SELECT
  c.company_name,
  m.*
FROM `PROJECT_ID.DATASET_ID.meta_campaign_daily` m
JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = m.company_id;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_page_crm` AS
SELECT
  c.company_name,
  l.*
FROM `PROJECT_ID.DATASET_ID.crm_leads_daily` l
JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = l.company_id;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_page_erp_orders` AS
SELECT
  c.company_name,
  o.*
FROM `PROJECT_ID.DATASET_ID.erp_orders_daily` o
JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = o.company_id;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_page_ga4` AS
SELECT
  c.company_name,
  g.*
FROM `PROJECT_ID.DATASET_ID.ga4_daily` g
JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = g.company_id;

CREATE OR REPLACE VIEW `PROJECT_ID.DATASET_ID.vw_page_audit` AS
SELECT
  c.company_name,
  a.*
FROM `PROJECT_ID.DATASET_ID.mcp_audit_logs` a
LEFT JOIN `PROJECT_ID.DATASET_ID.companies` c
  ON c.company_id = a.company_id;

