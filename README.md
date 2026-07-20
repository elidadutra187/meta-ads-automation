# Meta Ads Automation

**AI-assisted Meta Ads operations system for copy generation, creative organization, campaign support and performance monitoring.**

This project explores how local AI, Python and the Meta Marketing API can support paid media routines without removing human validation from sensitive decisions.

Repository: [elidadutra187/meta-ads-automation](https://github.com/elidadutra187/meta-ads-automation)

---

## Business problem

Paid media operations involve many repetitive tasks: organizing creatives, generating copy variations, checking campaign status, reading performance metrics, identifying weak ads and preparing optimization notes.

The goal of this project is not to blindly automate advertising decisions, but to create a safer workflow where AI helps with analysis and operational speed while the human still validates campaign changes.

---

## What it does

The system supports:

- local AI copy generation with Ollama;
- creative organization for Meta campaigns;
- campaign creation support through CLI;
- campaign listing and status checks;
- insights monitoring;
- reports for CTR, CPC, CPA, ROAS and performance;
- optimization suggestions based on rules;
- Windows setup scripts;
- structure prepared for MCP / Claude workflows.

---

## Cloud MCP: Meta + Google

The remote multi-company MCP entrypoint is `src/mcp_cloud.py`.

It is intentionally focused on Meta + Google for new companies:

- Meta Ads and Meta CAPI;
- Google Ads, GA4, GTM, Search Console and BigQuery/Looker;
- BigQuery-backed company registry and audit;
- Bearer-token authentication on `/mcp`;
- no ERP/CRM tools for new cloud companies.

Operational files:

- `Dockerfile`
- `.env.cloud.example`
- `scripts/deploy_cloud_run_meta_google.bat`
- `CLOUD_MCP_META_GOOGLE.md`
- `ERP_TINY_SHEETS_INTEGRATION.md`

Remote MCP endpoint after deploy:

```text
https://SEU-SERVICO.run.app/mcp
Authorization: Bearer <MCP_API_KEY>
```

## Multi-client isolation

The repository now includes explicit per-company routing files for:

- client catalog: `clients.config.json`
- Composio projects/accounts: `composio.accounts.json`
- Google asset mapping: `google.mapping.json`
- Meta asset mapping: `meta.mapping.json`
- Trello board mapping: `trello.mapping.json`
- Looker mapping: `looker.mapping.json`
- MCP policy: `mcp.tools.config.json`
- validation checklist: `VALIDATION_CHECKLIST.md`

Current client IDs:

- `saldao`
- `inspire`
- `nordeste`

Safety rules now expected by the MCP surface:

- company-scoped tools must receive `company_id`
- each company should use its own Composio project and API key
- each company should use a stable Composio `user_id`
- aliases must be unique per company and service
- sensitive Meta actions still require dry-run plus confirmation code
- Looker Studio assets must be mapped per company before use

Recommended Composio model:

- one Composio project per client
- one stable `user_id` per client inside that project
- one alias per toolkit/account, e.g. `meta_ads_inspire`
- use `connected_account_id` when an alias is not enough to remove ambiguity

Current Composio-first scope in this repo:

- included: Google Ads, GA4, Search Console, GTM, Meta Ads, Facebook/Meta Business, Trello
- excluded until official toolkit support is confirmed: Tiny ERP, Multigrow CRM

Recommended env model:

- `COMPOSIO_API_KEY_SALDAO`
- `COMPOSIO_API_KEY_INSPIRE`
- `COMPOSIO_API_KEY_NORDESTE`
- `COMPOSIO_ORG_API_KEY` for automatic project creation
- `COMPOSIO_CALLBACK_URL_SALDAO`, `COMPOSIO_CALLBACK_URL_INSPIRE`, `COMPOSIO_CALLBACK_URL_NORDESTE` when a custom callback is required
- `SALDAO_*`, `INSPIRE_*`, `NORDESTE_*` for service-specific IDs

The legacy unscoped env fallback should only be treated as temporary compatibility for Saldão.

### Provisioning Composio projects

To provision the Composio layer first, per company, use:

```bash
venv\Scripts\python.exe scripts\setup_composio_multi_client.py --companies inspire nordeste
```

This flow:

- reuses `clients.config.json` and `composio.accounts.json`
- expects one Composio project per company
- generates auth links for Google Ads, GA4, Search Console, Sheets, Drive, Gmail, BigQuery, Meta Ads, Meta Business and Trello
- writes the validation output to `COMPOSIO_VALIDATION_LINKS.md`

To create projects automatically, set `COMPOSIO_ORG_API_KEY`.
If the projects already exist, set `COMPOSIO_API_KEY_INSPIRE` and `COMPOSIO_API_KEY_NORDESTE` with the project keys from Composio before running the script.

## Looker Studio boundary

This repo treats Looker Studio as a mapped reporting surface, not as a fully code-driven dashboard editor.

Practical rule:

- Google Ads, GA4 and Search Console can often feed Looker Studio directly
- Meta Ads should default to `BigQuery` or `Google Sheets` as an intermediate layer unless the chosen connector is confirmed
- the official Data Studio / Looker Studio APIs are suitable for asset management and template/linking flows, not full visual report editing

For that reason, `looker.mapping.json` stores report/data-source mapping and `LOOKER_STUDIO_MULTIEMPRESA.md` documents the warehouse-first pattern.

---

## Stack

- **Python** for CLI and automation logic
- **Meta Marketing API** for campaign and insights access
- **Ollama** for local AI copy generation
- **MCP / Claude-ready architecture** for AI-assisted operations
- **Batch scripts** for Windows setup and execution
- **dotenv** for environment configuration

---

## Safety principle

This project is designed around a human-in-the-loop approach.

AI can generate copy, organize hypotheses, suggest adjustments and accelerate analysis. However, sensitive actions such as activating, pausing or changing real-budget campaigns should remain under explicit human validation.

---

## Example workflow

```text
Creative folder
→ AI copy generation
→ Campaign structure support
→ Meta Ads upload / campaign operations
→ Insights monitoring
→ Optimization report
→ Human review
→ Approved changes
```

---

## Main features

- Generate ad copy variations with local AI
- Upload and organize creatives
- Create structured campaign drafts
- Read campaign metrics
- Monitor performance indicators
- Generate reports and optimization notes
- Support repeatable campaign operations

---

## Metrics monitored

- CTR
- CPC
- CPM
- CPA
- ROAS
- spend
- impressions
- clicks
- conversions
- creative performance

---

## Why it matters

For small marketing teams, campaign management can become fragmented across spreadsheets, ad platforms, creative folders and manual notes.

This project creates a more structured operating layer between paid media execution, AI assistance and performance analysis.

---

## Status

Portfolio case / evolving project.

This project represents practical work in **Marketing Automation, Paid Media Operations and AI-assisted campaign workflows**.

---

## MCP surface

O MCP local foi retirado da superfície principal deste repositório.

Agora o caminho padrão é:

- `Composio Connect MCP` para Google Ads, GA4, Search Console, GTM, Meta Ads e Trello
- `Looker Studio` como camada de relatório mapeada por empresa
- `BigQuery` ou `Google Sheets` como camada intermediária quando necessário, principalmente para Meta

Os arquivos `mcp-config.json` e `claude_desktop_config.json` agora apontam para `https://connect.composio.dev/mcp`, com uma entrada separada por empresa.

---

## Author

**Élida Dutra**  
Growth · Paid Media · Marketing Automation · AI Workflows · E-commerce Ops

[LinkedIn](https://www.linkedin.com/in/elidadutra) · [GitHub](https://github.com/elidadutra187)

---

## Technical usage

### Verificar conexões

Coloque suas imagens na pasta `criativos/` e execute:

```bash
python -m src.main upload
```

Ou especifique uma pasta:

```bash
python -m src.main upload "C:\meus\criativos"
```

### Gerar copy com IA

```bash
python -m src.main gerar-copy "Curso de Marketing Digital" \
  --publico "Empreendedores 25-45 anos" \
  --objetivo "Vendas" \
  --tom "Urgente"
```

### Criar campanha completa

```bash
python -m src.main criar-campanha "Meu Produto" "https://meusite.com/produto" \
  --budget 5000 \
  --ativar
```

Isso vai:
1. Fazer upload de todos os criativos
2. Gerar copy com IA
3. Criar campanha, ad set e ads
4. Ativar (se usar `--ativar`)

### Listar campanhas

```bash
python -m src.main listar
```

### Ver métricas

```bash
python -m src.main insights CAMPAIGN_ID
```

### Otimizar campanhas

```bash
python -m src.main otimizar
```

Por padrão, esse comando só analisa e simula ações. Para executar alterações reais, use explicitamente:

```bash
python -m src.main otimizar --auto
```

### Monitoramento contínuo

```bash
python -m src.main monitorar --intervalo 30
```

### Gerar relatório

```bash
python -m src.main relatorio
```

## Estrutura do Projeto

```
meta-ads-automation/
├── config/
│   └── settings.py      # Configurações
├── criativos/           # Suas imagens/vídeos
├── logs/                # Logs do sistema
├── scripts/
│   ├── setup.bat        # Setup Windows
│   ├── run.bat          # Atalho para comandos
│   └── start_ollama.bat # Iniciar Ollama
├── src/
│   ├── main.py          # CLI principal
│   ├── meta_api.py      # Integração Meta
│   ├── ollama_copy.py   # Geração de copy
│   ├── campaign_manager.py # Gerenciador
│   ├── optimizer.py     # Otimização
│   └── monitor.py       # Monitoramento
├── templates/
│   └── prompts.py       # Prompts para IA
├── .env.example         # Exemplo de config
├── requirements.txt     # Dependências
└── README.md
```

## Regras de Otimização

O sistema aplica automaticamente:

| Condição | Ação |
|----------|------|
| CPA > limite | Pausar campanha |
| ROAS < mínimo | Reduzir budget 30% |
| CTR < 0.5% | Sugerir novo criativo |
| Performance boa | Aumentar budget 20% |

Configure os limites no `.env`:

```env
MAX_CPA=5000      # R$ 50,00 em centavos
MIN_ROAS=1.5      # ROAS mínimo
```

## Modelos Ollama Recomendados

| Modelo | RAM | Qualidade | Velocidade |
|--------|-----|-----------|------------|
| `llama3.2:3b` | 4GB | Boa | Rápida |
| `llama3.2` | 8GB | Muito boa | Média |
| `mistral` | 6GB | Boa | Rápida |
| `gemma2:9b` | 10GB | Excelente | Média |

Para trocar o modelo, edite o `.env`:

```env
OLLAMA_MODEL=mistral
```

## Fluxo de Automação

```
Seus Criativos (pasta)
        │
        ▼
   Upload Meta
        │
        ▼
  Ollama gera Copy ──────┐
        │                │
        ▼                │
 Criar Campanha          │
        │                │
        ▼                │
   Monitorar ◄───────────┘
        │
        ▼
   CPA/ROAS OK? ──No──► Pausar/Ajustar
        │
       Yes
        ▼
     Escalar
```

## Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## Suporte

- Issues: [GitHub Issues](https://github.com/seu-usuario/meta-ads-automation/issues)
- Docs Meta: [Marketing API](https://developers.facebook.com/docs/marketing-apis/)
- Docs Ollama: [ollama.com](https://ollama.com)
