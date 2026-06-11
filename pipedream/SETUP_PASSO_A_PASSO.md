# Setup Pipedream - Passo a Passo

## 1. Criar Conta
1. Acesse https://pipedream.com
2. Clique **Sign Up Free**
3. Use **Continue with Google** (mais rapido)

## 2. Criar Workflow

### Passo 1: Novo Workflow
1. Clique no botao **+ New** (canto superior direito)
2. Selecione **Workflow**
3. Escolha **HTTP / Webhook** como trigger
4. Clique **Save and continue**

### Passo 2: Copiar URL do Webhook
- Voce vera uma URL tipo: `https://eo1a2b3c4d.m.pipedream.net`
- **COPIE ESSA URL** - ela sera usada para chamar o workflow

### Passo 3: Adicionar Step do Google Analytics
1. Clique em **+** abaixo do trigger
2. Busque **Google Analytics Data**
3. Selecione **Run Report**
4. Clique em **Connect Google Analytics Data**
5. Autorize com sua conta Google
6. Configure:
   - Property ID: `properties/SEU_PROPERTY_ID` (encontre no GA4)
   - Start Date: `7daysAgo`
   - End Date: `today`
   - Metrics: `sessions, totalUsers, screenPageViews`

### Passo 4: Retornar Dados
1. Clique em **+** abaixo do step do GA
2. Busque **Node.js**
3. Selecione **Run Node.js code**
4. Cole este codigo:

```javascript
export default defineComponent({
  async run({ steps }) {
    return {
      success: true,
      source: "Saldao Center",
      data: steps.google_analytics_data.$return_value
    };
  }
});
```

### Passo 5: Deploy
1. Clique em **Deploy** (canto superior direito)
2. Confirme

## 3. Testar

### Via Terminal/Postman:
```bash
curl -X POST https://[SUA-URL].m.pipedream.net \
  -H "Content-Type: application/json" \
  -d '{"action": "test"}'
```

### Via Claude/ChatGPT:
Mande a mensagem:
```
Faca uma requisicao POST para https://[SUA-URL].m.pipedream.net
com body: {"action": "test"}
```

## 4. Compartilhar

Envie a URL para qualquer pessoa:
```
https://[SUA-URL].m.pipedream.net
```

Eles podem usar em qualquer IA (Claude, ChatGPT, etc).

---

## URLs que voce tera:

Depois de configurar, sua URL sera algo como:
```
https://eo1a2b3c4d.m.pipedream.net
```

## Como encontrar o Property ID do GA4:

1. Acesse https://analytics.google.com
2. Clique em **Admin** (engrenagem)
3. Em **Property**, clique em **Property Settings**
4. Copie o **Property ID** (numero)

---

## Troubleshooting

### "Nao consigo conectar Google Analytics"
- Verifique se sua conta Google tem acesso ao GA4
- Tente reconectar em Pipedream > Accounts

### "Erro 403"
- O Property ID pode estar errado
- Verifique as permissoes no GA4

### "Nao retorna dados"
- Verifique se o site tem trafego no periodo
- Tente periodo maior (30daysAgo)
