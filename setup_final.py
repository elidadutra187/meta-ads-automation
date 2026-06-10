# -*- coding: utf-8 -*-
"""
Setup Final - Saldao Center
Configura Composio + MCPs externos
"""
import httpx
import json

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
BASE_URL = "https://backend.composio.dev/api/v3"
USER_ID = "saldao-center"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Servicos disponiveis no Composio
COMPOSIO_SERVICOS = [
    {"slug": "facebook", "nome": "Facebook Pages"},
    {"slug": "googleads", "nome": "Google Ads"},
]

print("=" * 60)
print("SETUP FINAL - SALDAO CENTER")
print("=" * 60)

# 1. Listar auth configs existentes
print("\n1. AUTH CONFIGS EXISTENTES:")
response = httpx.get(f"{BASE_URL}/auth_configs", headers=headers, timeout=30)
configs = response.json().get("items", [])
existing_slugs = {}
for cfg in configs:
    tk = cfg.get("toolkit", {})
    slug = tk.get("slug")
    if slug:
        existing_slugs[slug] = cfg.get("id")
        print(f"   - {slug}: {cfg.get('id')}")

# 2. Criar auth configs faltantes
print("\n2. CRIANDO AUTH CONFIGS FALTANTES:")
for srv in COMPOSIO_SERVICOS:
    if srv["slug"] in existing_slugs:
        print(f"   {srv['nome']}: Ja existe")
        continue

    print(f"   {srv['nome']}: Criando...")
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
        print(f"      OK - ID: {data.get('id')}")
    else:
        print(f"      Erro: {response.text[:150]}")

# 3. Criar conexoes e obter links OAuth
print("\n3. GERANDO LINKS DE AUTORIZACAO:")
links = []

for srv in COMPOSIO_SERVICOS:
    auth_id = existing_slugs.get(srv["slug"])
    if not auth_id:
        continue

    print(f"   {srv['nome']}...")
    payload = {
        "user_id": USER_ID,
        "auth_config_id": auth_id,
    }
    response = httpx.post(f"{BASE_URL}/connected_accounts", headers=headers, json=payload, timeout=30)

    if response.status_code in [200, 201]:
        data = response.json()
        url = data.get("redirect_url") or data.get("url")
        if url:
            links.append({"nome": srv["nome"], "url": url})
            print(f"      Link gerado!")
        else:
            conn_id = data.get("id") or data.get("nanoid")
            status = data.get("status")
            print(f"      Conexao: {conn_id} | Status: {status}")
    else:
        print(f"      Erro: {response.text[:100]}")

# 4. Mostrar configuracao final
print("\n" + "=" * 60)
print("CONFIGURACAO FINAL")
print("=" * 60)

print("\n--- VIA COMPOSIO ---")
if links:
    print("\nLinks para autorizar (abra no navegador):")
    for i, link in enumerate(links, 1):
        print(f"\n{i}. {link['nome']}:")
        print(f"   {link['url']}")
else:
    print("\nConexoes ja configuradas ou pendentes.")

print("\n--- VIA MCP EXTERNO ---")
print("""
Os seguintes servicos NAO estao no Composio e precisam de MCP separado:

1. META ADS (MCP Oficial):
   URL: https://mcp.facebook.com/ads
   -> Acesse e faca login com sua conta Business

2. GOOGLE ANALYTICS 4 (Stape MCP):
   URL: https://mcp-ga.stape.ai/mcp
   -> Acesse e conecte sua conta Google

3. GOOGLE TAG MANAGER (Stape MCP):
   URL: https://mcp-gtm.stape.ai/mcp
   -> Acesse e conecte sua conta Google
""")

print("\n--- URL MCP COMPOSIO ---")
print(f"\nPara usar no Claude Desktop/Code:")
print(f"https://mcp.composio.dev/saldao-center/{API_KEY}")

print("\n" + "=" * 60)
print("PROXIMOS PASSOS:")
print("=" * 60)
print("""
1. Abra cada link acima e autorize
2. No Claude Desktop, va em Settings > Integrations
3. Adicione cada MCP URL
4. Reinicie o Claude

Depois disso, voce podera pedir:
- "Liste minhas campanhas do Meta Ads"
- "Qual o CTR no GA4 essa semana?"
- "Crie um post no Facebook"
""")
