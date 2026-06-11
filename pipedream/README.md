# Pipedream - Saldao Center MCP Hub

Workflows para integrar Google Analytics, Google Ads e Meta Ads com qualquer IA.

## Como Configurar

### 1. Criar conta no Pipedream
- Acesse: https://pipedream.com
- Login com Google (mais rapido)

### 2. Criar novo Workflow
- Clique em **New** > **Workflow**
- Escolha **HTTP / Webhook** como trigger

### 3. Copiar o codigo
- Adicione um step **Node.js**
- Cole o codigo de `workflow_hub.js`

### 4. Conectar Google
- No Pipedream, va em **Accounts**
- Conecte sua conta Google (Analytics, Ads)

### 5. Publicar
- Clique em **Deploy**
- Copie a URL gerada

## URL que sera gerada

```
https://eo[seu-id].m.pipedream.net
```

## Como usar em IAs

### Claude.ai
Adicione nas instrucoes do chat:
```
Use este endpoint para dados de marketing:
https://eo[seu-id].m.pipedream.net

Endpoints disponiveis:
- POST /analytics - Dados do Google Analytics
- POST /ads - Dados do Google Ads
- POST /meta - Dados do Meta Ads
```

### ChatGPT (Custom GPT)
Configure como Action com a URL do webhook.

### Qualquer IA
Faca requisicao HTTP para a URL.

## Compartilhar com outras pessoas

Basta enviar a URL do webhook. Qualquer pessoa pode usar em qualquer IA.
