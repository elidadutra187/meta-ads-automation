# -*- coding: utf-8 -*-
"""Setup Composio para Saldao Center"""
import httpx
import json

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
BASE_URL = "https://backend.composio.dev/api/v3"
USER_ID = "saldao-center"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

servicos = [
    {"slug": "metaads", "nome": "Meta Ads"},
    {"slug": "facebook", "nome": "Facebook"},
    {"slug": "googleanalytics", "nome": "Google Analytics"},
    {"slug": "googleads", "nome": "Google Ads"},
]

print("=" * 60)
print("COMPOSIO SETUP - SALDAO CENTER")
print("=" * 60)

auth_configs = {}

# 1. Criar auth configs
print("\n1. CRIANDO AUTH CONFIGS...")
for srv in servicos:
    print(f"\n   {srv['nome']}...")

    # Formato correto conforme documentacao
    payload = {
        "toolkit": {
            "slug": srv["slug"]
        },
        "auth_config": {
            "type": "use_composio_managed_auth",
            "credentials": {},
            "restrict_to_following_tools": []
        }
    }

    response = httpx.post(
        f"{BASE_URL}/auth_configs",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"      Status: {response.status_code}")

    if response.status_code in [200, 201]:
        data = response.json()
        auth_id = data.get("id") or data.get("nanoid")
        auth_configs[srv["slug"]] = auth_id
        print(f"      OK - ID: {auth_id}")
    elif response.status_code == 409:
        print(f"      Ja existe, buscando...")
        list_resp = httpx.get(
            f"{BASE_URL}/auth_configs",
            headers=headers,
            timeout=30
        )
        items = list_resp.json().get("items", [])
        for item in items:
            tk = item.get("toolkit", {})
            if tk.get("slug") == srv["slug"]:
                auth_configs[srv["slug"]] = item.get("id")
                print(f"      Encontrado - ID: {item.get('id')}")
                break
    else:
        error_text = response.text[:300] if response.text else "Sem detalhes"
        print(f"      Erro: {error_text}")

# 2. Criar conexoes
print("\n2. CRIANDO CONEXOES (gerando links OAuth)...")
links = []

for srv in servicos:
    auth_id = auth_configs.get(srv["slug"])
    if not auth_id:
        print(f"\n   {srv['nome']}: Sem auth config")
        continue

    print(f"\n   {srv['nome']}...")

    payload = {
        "user_id": USER_ID,
        "auth_config_id": auth_id,
        "redirect_url": "https://saldaocenter.com.br"
    }

    response = httpx.post(
        f"{BASE_URL}/connected_accounts",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"      Status: {response.status_code}")

    if response.status_code in [200, 201]:
        data = response.json()
        url = data.get("redirect_url") or data.get("url") or data.get("connection_url")
        if url:
            links.append({"nome": srv["nome"], "url": url})
            print(f"      Link OK!")
        else:
            # Talvez ja conectado
            status = data.get("status")
            if status:
                print(f"      Status: {status}")
            print(f"      Dados: {json.dumps(data)[:200]}")
    else:
        print(f"      Erro: {response.text[:200]}")

# 3. Mostrar links
print("\n" + "=" * 60)
print("LINKS PARA AUTORIZAR (abra no navegador):")
print("=" * 60)

if links:
    for i, link in enumerate(links, 1):
        print(f"\n{i}. {link['nome']}:")
        print(f"   {link['url']}")
else:
    print("\nVerificando se ja existem conexoes...")

# 4. Verificar conexoes
print("\n" + "=" * 60)
print("CONEXOES NO COMPOSIO:")
print("=" * 60)

response = httpx.get(
    f"{BASE_URL}/connected_accounts",
    headers=headers,
    timeout=30
)

if response.status_code == 200:
    data = response.json()
    items = data.get("items", [])
    if items:
        for item in items:
            tk = item.get("toolkit", {})
            print(f"   - {tk.get('slug', '?')}: {item.get('status', '?')}")
    else:
        print("   Nenhuma conexao")

print("\n" + "=" * 60)
print("URL MCP PARA CLAUDE:")
print("=" * 60)
print(f"\nhttps://mcp.composio.dev/{API_KEY}")
print("\nCole esta URL no Claude Desktop > Settings > Integrations")
