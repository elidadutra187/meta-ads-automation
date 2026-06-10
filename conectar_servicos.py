# -*- coding: utf-8 -*-
"""
Conectar servicos ao Composio - Saldao Center
"""
import httpx
import json
import webbrowser

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
BASE_URL = "https://backend.composio.dev/api/v3"
USER_ID = "saldao-center"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Servicos para conectar
SERVICOS = [
    {"slug": "metaads", "nome": "Meta Ads (Facebook/Instagram Ads)"},
    {"slug": "facebook", "nome": "Facebook Pages"},
    {"slug": "googleanalytics", "nome": "Google Analytics 4"},
    {"slug": "googleads", "nome": "Google Ads"},
]

def criar_auth_config(toolkit_slug: str):
    """Cria config de autenticacao."""
    try:
        response = httpx.post(
            f"{BASE_URL}/auth_configs",
            headers=headers,
            json={
                "toolkit_slug": toolkit_slug,
                "use_composio_auth": True
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 409:
            # Ja existe, buscar
            list_response = httpx.get(
                f"{BASE_URL}/auth_configs",
                headers=headers,
                params={"toolkit_slugs": toolkit_slug},
                timeout=30
            )
            items = list_response.json().get("items", [])
            if items:
                return items[0]
        return {"erro": response.text}
    except Exception as e:
        return {"erro": str(e)}

def iniciar_conexao(toolkit_slug: str, auth_config_id: str):
    """Inicia fluxo OAuth."""
    try:
        response = httpx.post(
            f"{BASE_URL}/connected_accounts/link",
            headers=headers,
            json={
                "user_id": USER_ID,
                "auth_config_id": auth_config_id
            },
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"erro": str(e)}

def conectar_servico(servico: dict):
    """Conecta um servico e retorna URL de auth."""
    print(f"\n{'='*50}")
    print(f"Conectando: {servico['nome']}")
    print('='*50)

    # 1. Criar/obter auth config
    print("1. Criando configuracao de auth...")
    auth = criar_auth_config(servico["slug"])

    if "erro" in auth:
        print(f"   Erro: {auth['erro'][:100]}")
        return None

    auth_id = auth.get("id") or auth.get("nanoid")
    print(f"   Auth Config ID: {auth_id}")

    # 2. Iniciar conexao
    print("2. Iniciando conexao OAuth...")
    conexao = iniciar_conexao(servico["slug"], auth_id)

    if "erro" in conexao:
        print(f"   Erro: {conexao['erro'][:100]}")
        return None

    # 3. Retornar URL
    url = conexao.get("redirect_url") or conexao.get("url")
    if url:
        print(f"3. URL de autorizacao gerada!")
        return url
    else:
        print(f"   Resposta: {json.dumps(conexao, indent=2)[:200]}")
        return None

def main():
    print("="*60)
    print("COMPOSIO - CONECTAR SERVICOS SALDAO CENTER")
    print("="*60)
    print(f"\nUser ID: {USER_ID}")
    print(f"API Key: {API_KEY[:10]}...")

    urls = []

    for servico in SERVICOS:
        url = conectar_servico(servico)
        if url:
            urls.append({"nome": servico["nome"], "url": url})

    # Resumo
    print("\n" + "="*60)
    print("LINKS PARA AUTORIZAR:")
    print("="*60)

    if urls:
        for i, item in enumerate(urls, 1):
            print(f"\n{i}. {item['nome']}:")
            print(f"   {item['url']}")

        print("\n" + "="*60)
        print("INSTRUCOES:")
        print("="*60)
        print("""
1. Clique em cada link acima
2. Faca login com a conta correspondente
3. Autorize o acesso
4. Volte aqui e execute 'verificar_conexoes.py'
        """)

        # Perguntar se quer abrir no navegador
        abrir = input("\nAbrir links no navegador? (s/n): ")
        if abrir.lower() == 's':
            for item in urls:
                webbrowser.open(item['url'])
                input(f"Pressione Enter apos autorizar {item['nome']}...")
    else:
        print("\nNenhum link gerado. Verifique os erros acima.")

if __name__ == "__main__":
    main()
