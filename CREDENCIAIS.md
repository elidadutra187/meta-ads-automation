# Guia de Credenciais - Saldão Center

Este guia mostra como obter cada credencial necessária para o MCP Hub.

## Arquitetura Completa

```
                    ┌─────────────────────────┐
                    │      CLAUDE / MCP       │
                    └───────────┬─────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │  Tiny   │ │Multigrow│ │   GTM   │ │   GA4   │ │  Meta   │
   │   ERP   │ │   CRM   │ │         │ │         │ │   Ads   │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │           │           │           │           │
   Produtos    Leads       Tags        Métricas   Campanhas
   Pedidos     Clientes    Triggers    Sessões    Anúncios
   Estoque     Negócios    Variáveis   Conversões Insights
```

---

## 1. TINY ERP (Olist)

### Onde obter
1. Acesse: https://tiny.com.br
2. Vá em: **Configurações > Integrações > API**
3. Clique em **Gerar Token**
4. Copie o token gerado

### No .env
```
TINY_TOKEN=seu_token_aqui
```

### Testar
```bash
curl "https://api.tiny.com.br/api2/produtos.pesquisa.php?token=SEU_TOKEN&formato=json"
```

---

## 2. MULTIGROW CRM

### Onde obter
1. Acesse o painel do Multigrow
2. Vá em: **Configurações > Integrações > API**
3. Gere uma nova API Key
4. Copie a URL da API e a Key

### No .env
```
MULTIGROW_API_URL=https://api.multigrow.com.br
MULTIGROW_API_KEY=sua_api_key
MULTIGROW_WEBHOOK_SECRET=seu_webhook_secret
```

### Webhook (opcional)
Configure o webhook para receber notificações de novos leads:
```
URL: https://seu-servidor.com/webhook/multigrow
Eventos: lead.created, lead.updated, deal.won
```

---

## 3. GOOGLE TAG MANAGER

### Onde obter Container ID
1. Acesse: https://tagmanager.google.com
2. Selecione sua conta
3. O Container ID está no formato: **GTM-XXXXXXX**

### No .env
```
GTM_CONTAINER_ID=GTM-XXXXXXX
GTM_ACCOUNT_ID=123456789
```

### Configurar MCP
1. Acesse: https://mcp.gtmeditor.com
2. Faça login com sua conta Google
3. Autorize o acesso ao GTM
4. Cole a URL no Claude Desktop

---

## 4. GOOGLE ANALYTICS 4

### Onde obter Property ID
1. Acesse: https://analytics.google.com
2. Vá em: **Admin > Property Settings**
3. Copie o **Property ID** (número)
4. Copie o **Measurement ID** (G-XXXXXXXXXX)

### No .env
```
GA4_PROPERTY_ID=123456789
GA4_MEASUREMENT_ID=G-XXXXXXXXXX
```

### Configurar MCP
1. Acesse: https://mcp-ga.stape.ai
2. Faça login com sua conta Google
3. Selecione a propriedade GA4
4. Cole a URL no Claude Desktop

---

## 5. GOOGLE ADS

### Onde obter
1. Acesse: https://ads.google.com
2. Clique no ícone de **Ferramentas** > **Configurações**
3. Copie o **Customer ID** (XXX-XXX-XXXX)

### Para Conversões
1. Vá em: **Ferramentas > Conversões**
2. Copie o **Conversion ID** (AW-XXXXXXXXX)

### No .env
```
GOOGLE_ADS_CUSTOMER_ID=123-456-7890
GOOGLE_ADS_CONVERSION_ID=AW-123456789
```

---

## 6. META ADS (Facebook/Instagram)

### Passo 1: Criar App
1. Acesse: https://developers.facebook.com
2. Clique em **Criar App**
3. Escolha: **Tipo: Business**
4. Nomeie: "Saldao Center Automation"

### Passo 2: Obter credenciais
1. No app, vá em **Configurações > Básico**
2. Copie: **App ID** e **App Secret**

### Passo 3: Gerar Access Token
1. Vá em: **Ferramentas > Graph API Explorer**
2. Selecione seu app
3. Adicione permissões:
   - `ads_management`
   - `ads_read`
   - `pages_read_engagement`
   - `business_management`
4. Clique em **Gerar Token de Acesso**
5. Copie o token

### Passo 4: Obter IDs
1. **Ad Account ID**: Business Manager > Contas de anúncio > Copie o número
2. **Page ID**: Página do Facebook > Sobre > ID da Página
3. **Pixel ID**: Gerenciador de Eventos > Pixels > Copie o ID

### No .env
```
META_APP_ID=123456789
META_APP_SECRET=abc123...
META_ACCESS_TOKEN=EAAG...
META_AD_ACCOUNT_ID=123456789
FACEBOOK_PAGE_ID=123456789
META_PIXEL_ID=123456789
```

### Usar MCP Oficial
1. Acesse: https://mcp.facebook.com/ads
2. Faça login com conta Business
3. Autorize o acesso
4. Cole a URL no Claude Desktop

---

## 7. OLLAMA (IA Local)

### Instalação
```bash
# Windows
winget install ollama

# Ou baixe de: https://ollama.com
```

### Baixar modelo
```bash
ollama pull llama3.2
```

### Iniciar
```bash
ollama serve
```

### No .env
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## Verificar Configurações

Execute o MCP Hub e teste:

```bash
cd D:\Users\elida\Desktop\GitHub-Prep\meta-ads-automation
.\venv\Scripts\python -m src.mcp_hub
```

No Claude, pergunte:
```
"status_integracoes"
```

Resposta esperada:
```json
{
  "tiny_erp": "OK",
  "multigrow": "OK",
  "gtm": "OK",
  "ga4": "OK",
  "meta_ads": "OK",
  "ollama": "OK"
}
```

---

## Fluxo Completo

Com tudo configurado, você pode fazer pelo Claude:

```
Você: "Liste os produtos do Tiny com estoque baixo"
Você: "Crie um anúncio no Meta para o porcelanato mais vendido"
Você: "Quanto gastamos em Meta Ads essa semana?"
Você: "Quantos leads entraram no Multigrow hoje?"
Você: "Qual o CTR médio no GA4 dos últimos 7 dias?"
```

---

## Suporte

- Tiny ERP: https://tiny.com.br/suporte
- Multigrow: Contate o suporte deles
- GTM/GA4: https://support.google.com/analytics
- Meta Ads: https://www.facebook.com/business/help
- MCP: https://modelcontextprotocol.io
