# -*- coding: utf-8 -*-
"""
Configurar Composio para Saldao Center via API v3.1
"""
import httpx
import json

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
BASE_URL = "https://backend.composio.dev/api/v3"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def listar_conexoes():
    """Lista conexoes do usuario."""
    try:
        response = httpx.get(
            f"{BASE_URL}/connected_accounts",
            headers=headers,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

def listar_toolkits():
    """Lista toolkits disponiveis."""
    try:
        response = httpx.get(
            f"{BASE_URL}/toolkits",
            headers=headers,
            params={"limit": 50},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

def obter_mcp_url():
    """Obtem URL do MCP endpoint."""
    try:
        response = httpx.get(
            f"{BASE_URL}/mcp/url",
            headers=headers,
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

def criar_auth_config(toolkit: str):
    """Cria configuracao de auth para um toolkit."""
    try:
        response = httpx.post(
            f"{BASE_URL}/auth_configs",
            headers=headers,
            json={
                "toolkit_slug": toolkit,
                "use_composio_auth": True
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

def iniciar_conexao(toolkit: str, user_id: str = "saldao-center"):
    """Inicia conexao OAuth."""
    try:
        # Primeiro criar auth config
        auth = criar_auth_config(toolkit)
        if "erro" in auth:
            return auth

        auth_config_id = auth.get("id") or auth.get("auth_config_id")

        # Iniciar conexao
        response = httpx.post(
            f"{BASE_URL}/connected_accounts/link",
            headers=headers,
            json={
                "user_id": user_id,
                "auth_config_id": auth_config_id
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

if __name__ == "__main__":
    print("=" * 60)
    print("COMPOSIO - CONFIGURACAO SALDAO CENTER")
    print("=" * 60)

    print("\n1. Verificando conexoes existentes...")
    conexoes = listar_conexoes()
    print(json.dumps(conexoes, indent=2, ensure_ascii=False)[:500])

    print("\n2. Obtendo URL MCP...")
    mcp = obter_mcp_url()
    print(json.dumps(mcp, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("TOOLKITS PARA CONECTAR:")
    print("=" * 60)
    print("""
Para conectar cada servico, acesse o Composio Dashboard:
https://app.composio.dev

Ou use os links de OAuth gerados pelo script.

Toolkits necessarios:
1. metaads - Meta Ads (Facebook/Instagram)
2. facebook - Facebook Pages
3. google_analytics - Google Analytics 4
4. googleads - Google Ads
5. google_tagmanager - Google Tag Manager (se disponivel)
""")
