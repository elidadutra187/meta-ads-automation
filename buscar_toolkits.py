# -*- coding: utf-8 -*-
import httpx

API_KEY = "ak_F86dMTnyUmU68-zYFM5i"
headers = {"x-api-key": API_KEY}
BASE = "https://backend.composio.dev/api/v3/toolkits"

termos = ["meta", "facebook", "google", "analytics", "ads", "tag"]

print("TOOLKITS DISPONIVEIS NO COMPOSIO")
print("=" * 50)

for termo in termos:
    response = httpx.get(BASE, headers=headers, params={"search": termo, "limit": 10}, timeout=30)
    items = response.json().get("items", [])
    if items:
        print(f"\nBusca: '{termo}'")
        for item in items:
            slug = item.get("slug", "?")
            name = item.get("name", "?")
            print(f"  - {slug}: {name}")
