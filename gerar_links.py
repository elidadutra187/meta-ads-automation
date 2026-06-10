# -*- coding: utf-8 -*-
"""Gerar links OAuth para Composio"""
import httpx
import json

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
BASE_URL = "https://backend.composio.dev/api/v3"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Auth configs existentes
AUTH_CONFIGS = {
    "facebook": "ac_xt8f3iVfWeV5",
    "googleads": "ac_xtdHb-rZ-cZG",
}

print("=" * 60)
print("GERANDO LINKS DE CONEXAO")
print("=" * 60)

for nome, auth_id in AUTH_CONFIGS.items():
    print(f"\n{nome.upper()}:")

    # Usando o endpoint link conforme documentacao nova
    payload = {
        "auth_config_id": auth_id,
        "user_id": "saldao-center",
        "redirect_url": "https://saldaocenter.com.br"
    }

    response = httpx.post(
        f"{BASE_URL}/connected_accounts/link",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"   Status: {response.status_code}")

    if response.status_code in [200, 201]:
        data = response.json()
        url = data.get("redirect_url") or data.get("url") or data.get("authorization_url")
        if url:
            print(f"   LINK: {url}")
        else:
            print(f"   Dados: {json.dumps(data, indent=2)}")
    else:
        print(f"   Erro: {response.text[:300]}")

print("\n" + "=" * 60)
print("LINKS MCP PARA ADICIONAR NO CLAUDE:")
print("=" * 60)
print(f"""
1. COMPOSIO (Facebook + Google Ads):
   https://mcp.composio.dev/saldao-center/{API_KEY}

2. META ADS OFICIAL:
   https://mcp.facebook.com/ads

3. GOOGLE ANALYTICS (Stape):
   https://mcp-ga.stape.ai/mcp

4. GOOGLE TAG MANAGER (Stape):
   https://mcp-gtm.stape.ai/mcp
""")
