# Guia de Configuração MCP - Saldão Center

Este guia mostra como integrar todas as APIs em um único lugar usando MCP.

## O que é MCP?

MCP (Model Context Protocol) é um protocolo que permite conectar IA (Claude) diretamente às suas ferramentas. Funciona como um "USB-C para IA" - uma conexão universal.

## Arquitetura Completa

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE DESKTOP/CODE                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
    ┌─────────┬───────────┼───────────┬─────────┬─────────┐
    ▼         ▼           ▼           ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ ┌───────┐
│ Meta  │ │  GA4  │ │   GTM   │ │  Local  │ │Google │ │ Stape │
│  Ads  │ │       │ │         │ │ Ollama  │ │  Ads* │ │Server │
└───┬───┘ └───┬───┘ └────┬────┘ └────┬────┘ └───┬───┘ └───┬───┘
    ▼         ▼          ▼           ▼         ▼         ▼
Campanhas  Métricas    Tags      Gerar    Campanhas  Containers
Anúncios   Sessões   Triggers    Copy     Conversões   Zones
Insights   Eventos   Variáveis Targeting    Ads      Hosting
```

**Atualizado em Junho 2026** - Inclui Google Analytics 4, GTM e Google Ads via Stape.ai

---

## Opção 1: Meta Ads MCP Oficial (Recomendado)

A Meta lançou um MCP oficial em abril de 2026.

### Configuração

1. Acesse: `https://mcp.facebook.com/ads`
2. Faça login com sua conta Meta Business
3. No Claude Desktop, vá em **Configurações > Integrações**
4. Cole a URL: `https://mcp.facebook.com/ads`

### Ferramentas Disponíveis (29 tools)

| Categoria | Ferramentas |
|-----------|-------------|
| Relatórios | Métricas, insights, breakdowns |
| Campanhas | Criar, pausar, ativar, editar |
| Catálogo | Produtos, feeds |
| Diagnóstico | Pixel, Conversions API |

---

## Opção 2: Google Analytics 4 MCP (Stape.ai)

Integração completa com GA4 para métricas e relatórios.

### Configuração

1. Acesse: `https://mcp-ga.stape.ai/mcp`
2. Faça login com sua conta Google
3. Autorize o acesso às propriedades GA4
4. A URL já está no `mcp-config.json`

### Ferramentas Disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `run_report` | Executa relatórios personalizados |
| `get_realtime` | Dados em tempo real |
| `list_properties` | Lista propriedades GA4 |
| `get_metrics` | Métricas (sessões, conversões, etc) |
| `list_google_ads` | Contas Google Ads vinculadas |

### Exemplos de Uso

```
Você: "Qual o tráfego do site essa semana?"
Você: "Quantas conversões tivemos ontem?"
Você: "De onde vem o tráfego? Orgânico ou pago?"
```

---

## Opção 3: Google Tag Manager MCP (Stape.ai)

Gerencie tags, triggers e variáveis pelo Claude.

### Configuração

1. Acesse: `https://gtm-mcp.stape.ai/mcp`
2. Faça login com sua conta Google
3. Autorize o acesso aos containers GTM

### Ferramentas Disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `list_containers` | Lista containers GTM |
| `list_tags` | Lista todas as tags |
| `create_tag` | Cria nova tag |
| `list_triggers` | Lista triggers |
| `create_trigger` | Cria novo trigger |
| `list_variables` | Lista variáveis |
| `publish_version` | Publica versão do container |

### Exemplos de Uso

```
Você: "Quais tags de conversão tenho no GTM?"
Você: "Crie uma tag de remarketing do Google Ads"
Você: "Liste os triggers de clique em botão"
```

---

## Opção 4: Pipeboard (42 ferramentas)

Mais completo que o oficial, inclui targeting detalhado.

### Instalação

```bash
npm install -g @pipeboard/meta-ads-mcp
```

### Configuração no Claude Desktop

Edite o arquivo `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "npx",
      "args": ["-y", "@pipeboard/meta-ads-mcp"],
      "env": {
        "META_ACCESS_TOKEN": "SEU_TOKEN_AQUI",
        "META_AD_ACCOUNT_ID": "SEU_AD_ACCOUNT_ID",
        "META_PAGE_ID": "SEU_PAGE_ID"
      }
    }
  }
}
```

---

## Opção 3: WhatsApp MCP (Wassenger)

Para gerenciar conversas e leads do WhatsApp.

### Criar conta

1. Acesse: https://wassenger.com
2. Conecte seu WhatsApp Business
3. Obtenha a API Key

### Configuração

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "npx",
      "args": ["-y", "@wassenger/mcp-server"],
      "env": {
        "WASSENGER_API_KEY": "SUA_API_KEY",
        "WASSENGER_DEVICE_ID": "SEU_DEVICE_ID"
      }
    }
  }
}
```

### Ferramentas

- Ler inbox
- Enviar mensagens
- Criar automações
- Gerenciar contatos
- Ver métricas de resposta

---

## Opção 4: MCP Local Saldão Center

Servidor local com Ollama para geração de copy.

### Executar

```bash
cd D:\Users\elida\Desktop\GitHub-Prep\meta-ads-automation
.\venv\Scripts\python -m src.mcp_server
```

### Ferramentas Disponíveis

| Ferramenta | Descrição |
|------------|-----------|
| `gerar_copy` | Gera copy com IA (Ollama) |
| `gerar_variacoes` | Cria variações para teste A/B |
| `listar_produtos` | Produtos do Saldão Center |
| `listar_diferenciais` | Ofertas e diferenciais |
| `obter_targeting` | Config para Baixada Santista |
| `sugerir_headlines` | Headlines prontos |
| `montar_link_whatsapp` | Link com mensagem pré-definida |
| `calcular_metragem` | Calcula m² necessário |
| `info_empresa` | Dados do Saldão Center |

### Configuração no Claude Code

```bash
claude mcp add saldao-local "D:\Users\elida\Desktop\GitHub-Prep\meta-ads-automation\venv\Scripts\python" -m src.mcp_server
```

---

## Configuração Completa (Tudo junto)

Para ter Meta Ads + WhatsApp + Local em um só lugar:

```json
{
  "mcpServers": {
    "meta-ads-oficial": {
      "type": "remote",
      "url": "https://mcp.facebook.com/ads"
    },
    "whatsapp": {
      "command": "npx",
      "args": ["-y", "@wassenger/mcp-server"],
      "env": {
        "WASSENGER_API_KEY": "SUA_KEY"
      }
    },
    "saldao-local": {
      "command": "D:\\Users\\elida\\Desktop\\GitHub-Prep\\meta-ads-automation\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "D:\\Users\\elida\\Desktop\\GitHub-Prep\\meta-ads-automation"
    }
  }
}
```

---

## Fluxo de Trabalho Completo

Com tudo integrado, você pode fazer pelo Claude:

```
Você: "Crie uma campanha de porcelanato 60x60 para Baixada Santista"

Claude:
1. [saldao-local] gerar_copy → Gera headline e texto
2. [saldao-local] obter_targeting → Pega config da região
3. [meta-ads] criar_campanha → Cria no Meta Ads
4. [saldao-local] montar_link_whatsapp → Prepara link de conversão
5. [whatsapp] enviar_template → Notifica equipe comercial
```

---

## Próximos Passos

1. **Escolha qual usar:**
   - Só Meta Ads → Opção 1 (Oficial)
   - Meta + Copy IA → Opção 1 + 4
   - Completo → Todas as opções

2. **Configure as credenciais:**
   - Meta Access Token
   - Page ID
   - Ad Account ID
   - (Opcional) Wassenger API Key

3. **Teste:**
   ```
   Você: "Liste os produtos do Saldão Center"
   Você: "Gere um copy para porcelanato acetinado"
   Você: "Qual o targeting da Baixada Santista?"
   ```

---

## Links Úteis

- [Meta Ads MCP Oficial](https://mcp.facebook.com/ads)
- [Pipeboard](https://github.com/pipeboard-co/meta-ads-mcp)
- [Wassenger](https://wassenger.com/integrations/claude)
- [Composio](https://composio.dev/toolkits/whatsapp)
- [Documentação MCP](https://modelcontextprotocol.io)
