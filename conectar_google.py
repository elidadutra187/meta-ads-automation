# -*- coding: utf-8 -*-
"""
Conectar Google Services - Saldao Center
Adiciona Google Analytics, Google Ads ao Composio
"""
import httpx
import webbrowser
import time

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
BASE_URL = "https://backend.composio.dev/api/v3"
USER_ID = "saldao-center"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Servicos Google para adicionar
GOOGLE_SERVICES = [
    {"slug": "google_analytics", "nome": "Google Analytics"},
    {"slug": "googleads", "nome": "Google Ads"},
    {"slug": "metaads", "nome": "Meta Ads (Facebook/Instagram)"},
]

print("=" * 60)
print("CONECTAR SERVICOS GOOGLE - SALDAO CENTER")
print("=" * 60)

# 1. Verificar auth configs existentes
print("\n1. VERIFICANDO AUTH CONFIGS...")
response = httpx.get(f"{BASE_URL}/auth_configs", headers=headers, timeout=30)
existing_slugs = {}
if response.status_code == 200:
    configs = response.json().get("items", [])
    for cfg in configs:
        tk = cfg.get("toolkit", {})
        slug = tk.get("slug")
        if slug:
            existing_slugs[slug] = cfg.get("id")
            print(f"   [OK] {tk.get('name', slug)}: {cfg.get('id')}")

# 2. Criar auth configs para servicos faltantes
print("\n2. CRIANDO AUTH CONFIGS FALTANTES...")
for srv in GOOGLE_SERVICES:
    if srv["slug"] in existing_slugs:
        print(f"   [JA EXISTE] {srv['nome']}")
        continue

    print(f"   [CRIANDO] {srv['nome']}...")
    payload = {
        "toolkit": {"slug": srv["slug"]},
        "auth_config": {
            "type": "use_composio_managed_auth",
            "credentials": {},
        }
    }
    response = httpx.post(f"{BASE_URL}/auth_configs", headers=headers, json=payload, timeout=30)
    if response.status_code in [200, 201]:
        data = response.json()
        existing_slugs[srv["slug"]] = data.get("id")
        print(f"      -> Criado: {data.get('id')}")
    else:
        print(f"      -> Erro: {response.text[:100]}")

# 3. Gerar links de autorizacao
print("\n3. GERANDO LINKS DE AUTORIZACAO...")
links = []

for srv in GOOGLE_SERVICES:
    auth_id = existing_slugs.get(srv["slug"])
    if not auth_id:
        print(f"   [SKIP] {srv['nome']}: Sem auth config")
        continue

    print(f"   [CONECTANDO] {srv['nome']}...")

    # Tentar criar conexao com redirect
    payload = {
        "integrationId": auth_id,
        "userUuid": USER_ID,
        "data": {},
        "redirectUri": "https://composio.dev/auth/callback",
    }

    response = httpx.post(
        f"{BASE_URL}/connectedAccounts",
        headers=headers,
        json=payload,
        timeout=30
    )

    if response.status_code in [200, 201]:
        data = response.json()
        url = data.get("redirectUrl") or data.get("connectionUrl") or data.get("url")
        if url:
            links.append({"nome": srv["nome"], "url": url, "slug": srv["slug"]})
            print(f"      -> Link gerado!")
        else:
            status = data.get("status")
            if status == "ACTIVE":
                print(f"      -> Ja conectado!")
            else:
                print(f"      -> Status: {status}")
                # Tentar iniciar conexao
                init_response = httpx.post(
                    f"{BASE_URL}/connectedAccounts/{data.get('id')}/initiate",
                    headers=headers,
                    timeout=30
                )
                if init_response.status_code == 200:
                    init_data = init_response.json()
                    url = init_data.get("redirectUrl") or init_data.get("url")
                    if url:
                        links.append({"nome": srv["nome"], "url": url, "slug": srv["slug"]})
                        print(f"      -> Link obtido via initiate!")
    else:
        error_msg = response.text[:150]
        print(f"      -> Erro: {error_msg}")

        # Tentar metodo alternativo
        alt_payload = {
            "auth_config_id": auth_id,
            "user_id": USER_ID,
        }
        alt_response = httpx.post(
            f"{BASE_URL}/connected_accounts",
            headers=headers,
            json=alt_payload,
            timeout=30
        )
        if alt_response.status_code in [200, 201]:
            data = alt_response.json()
            url = data.get("redirectUrl") or data.get("url") or data.get("redirect_url")
            if url:
                links.append({"nome": srv["nome"], "url": url, "slug": srv["slug"]})
                print(f"      -> Link obtido (metodo alt)!")

# 4. Mostrar resultados
print("\n" + "=" * 60)
print("LINKS DE AUTORIZACAO")
print("=" * 60)

if links:
    print("\nAbra cada link no navegador para autorizar:\n")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link['nome']}:")
        print(f"   {link['url']}\n")

    # Perguntar se quer abrir automaticamente
    print("-" * 40)
    resposta = input("Deseja abrir os links no navegador? (s/n): ").strip().lower()
    if resposta == 's':
        for link in links:
            print(f"Abrindo {link['nome']}...")
            webbrowser.open(link['url'])
            time.sleep(2)
else:
    print("\nNenhum link novo gerado.")
    print("Verifique se os servicos ja estao conectados.")

# 5. Instrucoes para MCP externos
print("\n" + "=" * 60)
print("SERVICOS QUE USAM MCP EXTERNO")
print("=" * 60)
print("""
Os seguintes servicos NAO estao no Composio e precisam ser
configurados diretamente no Claude Desktop:

1. GOOGLE TAG MANAGER (GTM):
   URL: https://mcp-gtm.stape.ai/mcp
   -> Acesse, faca login com Google e copie o MCP URL

2. GOOGLE ANALYTICS 4 (alternativa ao Composio):
   URL: https://mcp-ga.stape.ai/mcp
   -> Se preferir usar MCP direto em vez do Composio

3. META ADS (MCP Oficial Facebook):
   URL: https://mcp.facebook.com/ads
   -> Alternativa ao Composio com mais ferramentas
""")

print("\n" + "=" * 60)
print("CONFIGURACAO DO CLAUDE DESKTOP")
print("=" * 60)
print(f"""
Adicione estas URLs nas configuracoes do Claude:

1. Composio (todos os servicos):
   https://mcp.composio.dev/{USER_ID}/{API_KEY}

2. Google Tag Manager:
   [Obter URL em https://mcp-gtm.stape.ai]

3. Meta Ads Oficial:
   https://mcp.facebook.com/ads
""")

print("\nScript finalizado!")
