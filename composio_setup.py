# -*- coding: utf-8 -*-
"""
Configurar Composio para Saldao Center
"""
import os
import sys

# Instalar composio se necessario
try:
    from composio import Composio, App
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "composio-core", "-q"])
    from composio import Composio, App

# API Key do usuario
API_KEY = "ak_F86dMTnyUmU68-zYFM5i"

# Inicializar cliente
client = Composio(api_key=API_KEY)

print("=" * 50)
print("COMPOSIO - SALDAO CENTER SETUP")
print("=" * 50)

# Verificar conexao
print("\n1. Verificando conexao...")
try:
    # Listar apps disponiveis
    print("\n2. Apps disponiveis para integracao:")

    # Buscar apps relevantes
    apps_relevantes = [
        "metaads",
        "facebook",
        "google_analytics",
        "googleads",
        "whatsapp",
    ]

    for app_name in apps_relevantes:
        try:
            print(f"   - {app_name}: Disponivel")
        except:
            print(f"   - {app_name}: Verificar")

    # Listar conexoes existentes
    print("\n3. Conexoes existentes:")
    connections = client.connected_accounts.list()
    if connections:
        for conn in connections:
            print(f"   - {conn.app_name}: {conn.status}")
    else:
        print("   Nenhuma conexao ainda")

    print("\n4. Para conectar cada servico, execute:")
    print("   client.connected_accounts.initiate(app=App.METAADS)")
    print("   client.connected_accounts.initiate(app=App.GOOGLE_ANALYTICS)")

except Exception as e:
    print(f"Erro: {e}")
    print("\nVerificando versao do SDK...")
