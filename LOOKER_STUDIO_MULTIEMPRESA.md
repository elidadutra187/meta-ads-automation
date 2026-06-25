# Looker Studio Multiempresa

Este pacote prepara o SQL para um relatorio Looker Studio com uma pagina por empresa e fontes de dados organizadas.

## Arquivo SQL

Use:

```text
looker_studio/bigquery_multiempresa.sql
```

Antes de rodar, troque:

```text
PROJECT_ID
DATASET_ID
```

Exemplo recomendado:

```text
PROJECT_ID = seu-projeto-google-cloud
DATASET_ID = mcp_marketing_ops
```

## O que o SQL cria

Tabelas:

- `companies`
- `company_data_sources`
- `meta_campaign_daily`
- `crm_leads_daily`
- `erp_orders_daily`
- `ga4_daily`
- `mcp_audit_logs`

Views para o Looker Studio:

- `vw_looker_company_pages`
- `vw_looker_data_sources`
- `vw_page_company_overview_daily`
- `vw_page_meta_ads`
- `vw_page_crm`
- `vw_page_erp_orders`
- `vw_page_ga4`
- `vw_page_audit`

## Paginas no Looker Studio

Crie uma pagina por empresa usando `vw_looker_company_pages` como indice.

Pagina inicial:

- Fonte: `vw_looker_company_pages`
- Tabela: empresas conectadas
- Campo principal: `company_name`
- Campos de status: `connected_sources`, `total_sources`, `source_status_summary`

Pagina da empresa:

- Filtro de pagina: `company_id`
- Visao geral: `vw_page_company_overview_daily`
- Meta Ads: `vw_page_meta_ads`
- CRM: `vw_page_crm`
- ERP/Vendas: `vw_page_erp_orders`
- GA4/Site: `vw_page_ga4`
- Auditoria MCP: `vw_page_audit`
- Fontes conectadas: `vw_looker_data_sources`

Para cada nova empresa, duplique a pagina e altere o filtro `company_id`.

## Empresa inicial incluida

O SQL ja cria a empresa:

```text
company_id: saldao-center
company_name: Saldao Center
CRM: Multigrow
ERP: Tiny ERP / Olist
Google Sheet: 1SIrBdhLKB9TROzjciUkcyhUk9A4avaAtcUKE9IN3rYE
```

## Fontes de dados iniciais

Para `saldao-center`, o SQL registra:

- Meta Ads
- Tiny ERP / Olist
- Multigrow CRM
- Olist Vendas / Mes
- Composio
- GA4
- GTM

As fontes com token pendente entram como `pending_config`. As ja existentes entram como `configured_*`.

## Como conectar no Looker Studio

1. Abra o BigQuery.
2. Rode o SQL em `looker_studio/bigquery_multiempresa.sql`.
3. Abra o Looker Studio.
4. Crie uma fonte BigQuery para cada view `vw_*`.
5. Crie a pagina inicial com `vw_looker_company_pages`.
6. Duplique uma pagina modelo para cada empresa e filtre por `company_id`.

## Ambiente criado

Projeto Google Cloud configurado:

```text
steady-orb-447001-f0
```

Dataset criado:

```text
mcp_marketing_ops
```

Dataset completo:

```text
steady-orb-447001-f0.mcp_marketing_ops
```

Como o projeto ainda esta sem billing ativo, o setup foi executado em modo free tier:

- DDL e views via `bq query`
- dados iniciais via `bq load`
- sem `MERGE`/DML

Script para repetir o setup gratuito:

```bat
scripts\run_bigquery_setup_free_tier.bat
```

## Validacao feita

Tabelas com dados:

```text
companies: 1
company_data_sources: 5
mcp_audit_logs: 11
```

View principal validada:

```text
vw_looker_company_pages
company_id: saldao-center
company_name: Saldao Center
connected_sources: 4
total_sources: 5
```

Fontes validadas:

```text
composio: configured
google_sheets: configured_apps_script
metaads: pending_config
multigrow: configured_webhook
tiny: configured_local_env
```

## Fontes BigQuery para adicionar no Looker Studio

Use o conector BigQuery e selecione o projeto:

```text
steady-orb-447001-f0
```

Dataset:

```text
mcp_marketing_ops
```

Adicione estas views como fontes:

```text
vw_looker_company_pages
vw_looker_data_sources
vw_page_company_overview_daily
vw_page_meta_ads
vw_page_crm
vw_page_erp_orders
vw_page_ga4
vw_page_audit
```

## Proximo passo tecnico

Depois disso, o MCP precisa enviar snapshots para as tabelas:

- campanhas Meta em `meta_campaign_daily`
- leads CRM em `crm_leads_daily`
- pedidos ERP em `erp_orders_daily`
- metricas GA4 em `ga4_daily`
- logs MCP em `mcp_audit_logs`
