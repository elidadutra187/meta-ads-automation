@echo off
setlocal

set "PROJECT_ID=%BIGQUERY_PROJECT_ID%"
set "DATASET_ID=%BIGQUERY_DATASET_ID%"

if "%PROJECT_ID%"=="" set "PROJECT_ID=steady-orb-447001-f0"
if "%DATASET_ID%"=="" set "DATASET_ID=mcp_marketing_ops"

set "PATH=%USERPROFILE%\google-cloud-sdk-install\google-cloud-sdk\bin;%PATH%"
set "BIGQUERY_PROJECT_ID=%PROJECT_ID%"
set "BIGQUERY_DATASET_ID=%DATASET_ID%"

python scripts\render_bigquery_schema_views.py
python scripts\export_bigquery_load_jsonl.py

bq query --project_id=%PROJECT_ID% --use_legacy_sql=false --format=none < looker_studio\bigquery_schema_views_rendered.sql

bq load --project_id=%PROJECT_ID% --source_format=NEWLINE_DELIMITED_JSON %DATASET_ID%.companies data\bigquery_load\companies.jsonl
bq load --project_id=%PROJECT_ID% --source_format=NEWLINE_DELIMITED_JSON %DATASET_ID%.company_data_sources data\bigquery_load\company_data_sources.jsonl
bq load --project_id=%PROJECT_ID% --source_format=NEWLINE_DELIMITED_JSON %DATASET_ID%.mcp_audit_logs data\bigquery_load\mcp_audit_logs.jsonl

echo BigQuery/Looker setup finalizado para %PROJECT_ID%.%DATASET_ID%

