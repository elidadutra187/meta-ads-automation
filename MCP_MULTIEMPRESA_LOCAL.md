# MCP Multiempresa Local

Este projeto agora tem uma base local para operar varias empresas sem misturar contas, tokens ou logs.

## O que foi criado

- Cadastro de empresas em SQLite local: `data/mcp_local.db`.
- Conexoes por empresa: Meta Ads, Tiny, Multigrow, Google Sheets, Composio etc.
- Cofre local por empresa em `secrets/companies/<company_id>.json`.
- Auditoria em SQLite para chamadas do MCP e acoes Meta protegidas.
- Status seguro mostrando quantas empresas existem e onde esta o banco local.

## Ferramentas MCP novas

- `cadastrar_empresa`
- `listar_empresas`
- `registrar_conexao_empresa`
- `listar_conexoes_empresa`
- `salvar_segredo_empresa`
- `status_cofre_empresa`
- `listar_auditoria_mcp`

## Regras de seguranca

- Tokens nao devem ser gravados no banco.
- Tokens ficam em `secrets/companies/`, pasta ignorada pelo Git.
- O MCP retorna apenas mascara e fingerprint dos segredos.
- Toda chamada de ferramenta e registrada em `audit_logs`.
- Acoes Meta sensiveis continuam com dry-run, codigo de confirmacao e limite de budget.

## Empresa inicial

Foi cadastrada a empresa:

- `company_id`: `saldao-center`
- CRM: Multigrow
- ERP: Tiny ERP / Olist
- Google Sheet: `1SIrBdhLKB9TROzjciUkcyhUk9A4avaAtcUKE9IN3rYE`

As conexoes foram registradas como referencias operacionais. Nenhum token foi copiado para o banco.

## Antes do MCP online centralizado

1. Cadastrar cada empresa com `company_id` proprio.
2. Registrar as conexoes de cada empresa.
3. Salvar segredos locais somente quando necessario.
4. Validar auditoria com `listar_auditoria_mcp`.
5. Depois migrar o cofre para Supabase Vault, Render/Railway secrets ou AWS Secrets Manager.

