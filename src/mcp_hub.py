# -*- coding: utf-8 -*-
"""
MCP Hub - Saldao Center
Integra todos os sistemas em um unico servidor MCP:
- Tiny ERP (pedidos, estoque, produtos)
- Multigrow CRM (leads, clientes)
- Google Tag Manager (tags, triggers)
- Google Analytics 4 (metricas)
- Meta Ads API (campanhas, anuncios)
- WhatsApp (conversas)
"""
import os
import json
import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Ollama para IA
import ollama

# ==============================================================================
# CONFIGURACOES
# ==============================================================================

# Tiny ERP (Olist)
TINY_CONFIG = {
    "api_url": "https://api.tiny.com.br/api2",
    "token": os.getenv("TINY_TOKEN", ""),
}

# Multigrow CRM
MULTIGROW_CONFIG = {
    "api_url": os.getenv("MULTIGROW_API_URL", "https://api.multigrow.com.br"),
    "api_key": os.getenv("MULTIGROW_API_KEY", ""),
    "webhook_secret": os.getenv("MULTIGROW_WEBHOOK_SECRET", ""),
}

# Google Tag Manager
GTM_CONFIG = {
    "mcp_url": "https://mcp.gtmeditor.com",
    "container_id": os.getenv("GTM_CONTAINER_ID", ""),
}

# Google Analytics 4
GA4_CONFIG = {
    "mcp_url": "https://mcp-ga.stape.ai/mcp",
    "property_id": os.getenv("GA4_PROPERTY_ID", ""),
}

# Meta Ads
META_CONFIG = {
    "mcp_url": "https://mcp.facebook.com/ads",
    "access_token": os.getenv("META_ACCESS_TOKEN", ""),
    "ad_account_id": os.getenv("META_AD_ACCOUNT_ID", ""),
    "page_id": os.getenv("FACEBOOK_PAGE_ID", ""),
}

# Saldao Center
SALDAO_CONFIG = {
    "whatsapp": "5513997258292",
    "site": "https://saldaocenter.com.br",
}

# ==============================================================================
# SERVIDOR MCP
# ==============================================================================

server = Server("saldao-hub")

# Cliente HTTP global
http_client = httpx.AsyncClient(timeout=30.0)


# ==============================================================================
# FERRAMENTAS - TINY ERP
# ==============================================================================

async def tiny_request(endpoint: str, params: dict = None) -> dict:
    """Faz requisicao para Tiny ERP API."""
    if not TINY_CONFIG["token"]:
        return {"erro": "TINY_TOKEN nao configurado no .env"}

    url = f"{TINY_CONFIG['api_url']}/{endpoint}"
    params = params or {}
    params["token"] = TINY_CONFIG["token"]
    params["formato"] = "json"

    try:
        response = await http_client.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"erro": str(e)}


async def tiny_listar_produtos(pagina: int = 1) -> dict:
    """Lista produtos do Tiny ERP."""
    return await tiny_request("produtos.pesquisa.php", {"pagina": pagina})


async def tiny_consultar_estoque(produto_id: str) -> dict:
    """Consulta estoque de um produto."""
    return await tiny_request("produto.obter.estoque.php", {"id": produto_id})


async def tiny_listar_pedidos(situacao: str = None, pagina: int = 1) -> dict:
    """Lista pedidos do Tiny ERP."""
    params = {"pagina": pagina}
    if situacao:
        params["situacao"] = situacao
    return await tiny_request("pedidos.pesquisa.php", params)


async def tiny_obter_pedido(pedido_id: str) -> dict:
    """Obtem detalhes de um pedido."""
    return await tiny_request("pedido.obter.php", {"id": pedido_id})


async def tiny_listar_clientes(pagina: int = 1) -> dict:
    """Lista clientes do Tiny ERP."""
    return await tiny_request("contatos.pesquisa.php", {"pagina": pagina})


# ==============================================================================
# FERRAMENTAS - MULTIGROW CRM
# ==============================================================================

async def multigrow_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Faz requisicao para Multigrow CRM API."""
    if not MULTIGROW_CONFIG["api_key"]:
        return {"erro": "MULTIGROW_API_KEY nao configurado no .env"}

    url = f"{MULTIGROW_CONFIG['api_url']}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {MULTIGROW_CONFIG['api_key']}",
        "Content-Type": "application/json",
    }

    try:
        if method == "GET":
            response = await http_client.get(url, headers=headers, params=data)
        elif method == "POST":
            response = await http_client.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = await http_client.put(url, headers=headers, json=data)
        else:
            return {"erro": f"Metodo nao suportado: {method}"}

        return response.json()
    except Exception as e:
        return {"erro": str(e)}


async def multigrow_listar_leads(status: str = None) -> dict:
    """Lista leads do Multigrow CRM."""
    params = {}
    if status:
        params["status"] = status
    return await multigrow_request("GET", "leads", params)


async def multigrow_criar_lead(dados: dict) -> dict:
    """Cria novo lead no Multigrow CRM."""
    return await multigrow_request("POST", "leads", dados)


async def multigrow_atualizar_lead(lead_id: str, dados: dict) -> dict:
    """Atualiza lead no Multigrow CRM."""
    return await multigrow_request("PUT", f"leads/{lead_id}", dados)


async def multigrow_listar_negocios() -> dict:
    """Lista negocios/oportunidades do Multigrow."""
    return await multigrow_request("GET", "deals")


# ==============================================================================
# FERRAMENTAS - GOOGLE TAG MANAGER
# ==============================================================================

async def gtm_listar_tags(container_id: str = None) -> dict:
    """Lista tags do GTM."""
    container = container_id or GTM_CONFIG["container_id"]
    if not container:
        return {"erro": "GTM_CONTAINER_ID nao configurado"}

    # Usar MCP remoto do GTM
    try:
        response = await http_client.post(
            f"{GTM_CONFIG['mcp_url']}/tools/list_tags",
            json={"container_id": container}
        )
        return response.json()
    except Exception as e:
        return {"erro": str(e), "dica": "Configure o GTM MCP em mcp.gtmeditor.com"}


async def gtm_criar_tag_meta_pixel(pixel_id: str, evento: str) -> dict:
    """Cria tag do Meta Pixel no GTM."""
    return {
        "tipo": "Meta Pixel",
        "pixel_id": pixel_id,
        "evento": evento,
        "instrucoes": f"""
Para criar manualmente no GTM:
1. Acesse tagmanager.google.com
2. Nova Tag > Tipo: HTML Personalizado
3. Cole o codigo do Meta Pixel com evento {evento}
4. Trigger: Todas as paginas ou evento especifico
5. Publique o container
        """,
    }


# ==============================================================================
# FERRAMENTAS - GOOGLE ANALYTICS 4
# ==============================================================================

async def ga4_obter_metricas(
    data_inicio: str = None,
    data_fim: str = None,
    metricas: list = None
) -> dict:
    """Obtem metricas do GA4."""
    data_inicio = data_inicio or (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    data_fim = data_fim or datetime.now().strftime("%Y-%m-%d")
    metricas = metricas or ["sessions", "users", "conversions"]

    return {
        "property_id": GA4_CONFIG["property_id"],
        "periodo": f"{data_inicio} a {data_fim}",
        "metricas_solicitadas": metricas,
        "instrucoes": """
Para conectar GA4 via MCP:
1. Acesse stape.io e configure o GA4 MCP
2. Ou use o MCP oficial: developers.google.com/analytics/devguides/MCP
3. Autentique com sua conta Google
4. Cole a URL no Claude Desktop
        """,
    }


# ==============================================================================
# FERRAMENTAS - META ADS
# ==============================================================================

async def meta_listar_campanhas() -> dict:
    """Lista campanhas do Meta Ads."""
    if not META_CONFIG["access_token"]:
        return {"erro": "META_ACCESS_TOKEN nao configurado"}

    url = f"https://graph.facebook.com/v19.0/act_{META_CONFIG['ad_account_id']}/campaigns"
    params = {
        "access_token": META_CONFIG["access_token"],
        "fields": "id,name,status,objective,daily_budget",
    }

    try:
        response = await http_client.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"erro": str(e)}


async def meta_obter_insights(campaign_id: str, periodo: str = "last_7d") -> dict:
    """Obtem insights de uma campanha Meta."""
    if not META_CONFIG["access_token"]:
        return {"erro": "META_ACCESS_TOKEN nao configurado"}

    url = f"https://graph.facebook.com/v19.0/{campaign_id}/insights"
    params = {
        "access_token": META_CONFIG["access_token"],
        "date_preset": periodo,
        "fields": "impressions,clicks,spend,ctr,cpc,actions,cost_per_action_type",
    }

    try:
        response = await http_client.get(url, params=params)
        return response.json()
    except Exception as e:
        return {"erro": str(e)}


# ==============================================================================
# FERRAMENTAS - COPY IA (OLLAMA)
# ==============================================================================

async def gerar_copy_anuncio(produto: str, diferencial: str = "15x sem juros") -> dict:
    """Gera copy de anuncio usando Ollama."""
    prompt = f"""Voce e copywriter do Saldao Center (pisos e porcelanatos em Praia Grande/SP).

PRODUTO: {produto}
DIFERENCIAL: {diferencial}
OBJETIVO: Fazer a pessoa chamar no WhatsApp (13) 99725-8292

REGRAS:
- Tom direto, comercial, urgente
- Maximo 2 emojis
- Terminar com CTA para WhatsApp

Crie no formato JSON:
{{"headline": "max 40 chars", "texto": "max 125 chars", "descricao": "max 30 chars"}}

Responda APENAS o JSON."""

    try:
        response = ollama.generate(model="llama3.2", prompt=prompt)
        resultado = response["response"]

        # Tentar parsear JSON
        start = resultado.find("{")
        end = resultado.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(resultado[start:end])
        return {"texto": resultado}
    except Exception as e:
        return {"erro": str(e)}


# ==============================================================================
# REGISTRO DE FERRAMENTAS MCP
# ==============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas as ferramentas do hub."""
    return [
        # TINY ERP
        Tool(
            name="tiny_listar_produtos",
            description="Lista produtos do Tiny ERP (estoque, precos)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pagina": {"type": "integer", "description": "Pagina (padrao: 1)"}
                }
            }
        ),
        Tool(
            name="tiny_consultar_estoque",
            description="Consulta estoque de um produto no Tiny",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto_id": {"type": "string", "description": "ID do produto"}
                },
                "required": ["produto_id"]
            }
        ),
        Tool(
            name="tiny_listar_pedidos",
            description="Lista pedidos do Tiny ERP",
            inputSchema={
                "type": "object",
                "properties": {
                    "situacao": {"type": "string", "description": "Filtrar por situacao"},
                    "pagina": {"type": "integer"}
                }
            }
        ),
        Tool(
            name="tiny_obter_pedido",
            description="Obtem detalhes de um pedido especifico",
            inputSchema={
                "type": "object",
                "properties": {
                    "pedido_id": {"type": "string", "description": "ID do pedido"}
                },
                "required": ["pedido_id"]
            }
        ),
        Tool(
            name="tiny_listar_clientes",
            description="Lista clientes cadastrados no Tiny",
            inputSchema={
                "type": "object",
                "properties": {"pagina": {"type": "integer"}}
            }
        ),

        # MULTIGROW CRM
        Tool(
            name="multigrow_listar_leads",
            description="Lista leads do Multigrow CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filtrar por status"}
                }
            }
        ),
        Tool(
            name="multigrow_criar_lead",
            description="Cria novo lead no Multigrow",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "telefone": {"type": "string"},
                    "email": {"type": "string"},
                    "origem": {"type": "string", "description": "Ex: Meta Ads, Google, Organico"},
                    "interesse": {"type": "string", "description": "Produto de interesse"}
                },
                "required": ["nome", "telefone"]
            }
        ),
        Tool(
            name="multigrow_atualizar_lead",
            description="Atualiza status ou dados de um lead",
            inputSchema={
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "status": {"type": "string"},
                    "observacao": {"type": "string"}
                },
                "required": ["lead_id"]
            }
        ),

        # GOOGLE TAG MANAGER
        Tool(
            name="gtm_listar_tags",
            description="Lista tags configuradas no GTM",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_id": {"type": "string"}
                }
            }
        ),
        Tool(
            name="gtm_criar_tag_meta_pixel",
            description="Instrucoes para criar tag Meta Pixel no GTM",
            inputSchema={
                "type": "object",
                "properties": {
                    "pixel_id": {"type": "string", "description": "ID do Meta Pixel"},
                    "evento": {"type": "string", "description": "Ex: Purchase, Lead, AddToCart"}
                },
                "required": ["pixel_id", "evento"]
            }
        ),

        # GOOGLE ANALYTICS 4
        Tool(
            name="ga4_obter_metricas",
            description="Obtem metricas do Google Analytics 4",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_inicio": {"type": "string", "description": "YYYY-MM-DD"},
                    "data_fim": {"type": "string", "description": "YYYY-MM-DD"},
                    "metricas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Ex: sessions, users, conversions"
                    }
                }
            }
        ),

        # META ADS
        Tool(
            name="meta_listar_campanhas",
            description="Lista campanhas do Meta Ads (Facebook/Instagram)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="meta_obter_insights",
            description="Obtem metricas de uma campanha Meta",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string"},
                    "periodo": {
                        "type": "string",
                        "description": "last_7d, last_30d, today, yesterday"
                    }
                },
                "required": ["campaign_id"]
            }
        ),

        # COPY IA
        Tool(
            name="gerar_copy_anuncio",
            description="Gera copy de anuncio com IA (Ollama) para Saldao Center",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto": {"type": "string", "description": "Ex: Porcelanato 60x60"},
                    "diferencial": {"type": "string", "description": "Ex: 15x sem juros"}
                },
                "required": ["produto"]
            }
        ),

        # UTILITARIOS
        Tool(
            name="montar_link_whatsapp",
            description="Monta link do WhatsApp do Saldao Center",
            inputSchema={
                "type": "object",
                "properties": {
                    "mensagem": {"type": "string", "description": "Mensagem pre-definida"}
                }
            }
        ),
        Tool(
            name="status_integracoes",
            description="Verifica status de todas as integracoes",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Executa uma ferramenta."""

    result = {}

    # TINY ERP
    if name == "tiny_listar_produtos":
        result = await tiny_listar_produtos(arguments.get("pagina", 1))
    elif name == "tiny_consultar_estoque":
        result = await tiny_consultar_estoque(arguments["produto_id"])
    elif name == "tiny_listar_pedidos":
        result = await tiny_listar_pedidos(
            arguments.get("situacao"),
            arguments.get("pagina", 1)
        )
    elif name == "tiny_obter_pedido":
        result = await tiny_obter_pedido(arguments["pedido_id"])
    elif name == "tiny_listar_clientes":
        result = await tiny_listar_clientes(arguments.get("pagina", 1))

    # MULTIGROW CRM
    elif name == "multigrow_listar_leads":
        result = await multigrow_listar_leads(arguments.get("status"))
    elif name == "multigrow_criar_lead":
        result = await multigrow_criar_lead(arguments)
    elif name == "multigrow_atualizar_lead":
        lead_id = arguments.pop("lead_id")
        result = await multigrow_atualizar_lead(lead_id, arguments)

    # GTM
    elif name == "gtm_listar_tags":
        result = await gtm_listar_tags(arguments.get("container_id"))
    elif name == "gtm_criar_tag_meta_pixel":
        result = await gtm_criar_tag_meta_pixel(
            arguments["pixel_id"],
            arguments["evento"]
        )

    # GA4
    elif name == "ga4_obter_metricas":
        result = await ga4_obter_metricas(
            arguments.get("data_inicio"),
            arguments.get("data_fim"),
            arguments.get("metricas")
        )

    # META ADS
    elif name == "meta_listar_campanhas":
        result = await meta_listar_campanhas()
    elif name == "meta_obter_insights":
        result = await meta_obter_insights(
            arguments["campaign_id"],
            arguments.get("periodo", "last_7d")
        )

    # COPY IA
    elif name == "gerar_copy_anuncio":
        result = await gerar_copy_anuncio(
            arguments["produto"],
            arguments.get("diferencial", "15x sem juros")
        )

    # UTILITARIOS
    elif name == "montar_link_whatsapp":
        msg = arguments.get("mensagem", "Ola, vi o anuncio e quero saber mais!")
        msg_encoded = msg.replace(" ", "%20")
        result = {
            "link": f"https://wa.me/{SALDAO_CONFIG['whatsapp']}?text={msg_encoded}",
            "whatsapp": "(13) 99725-8292",
        }

    elif name == "status_integracoes":
        result = {
            "tiny_erp": "OK" if TINY_CONFIG["token"] else "NAO CONFIGURADO",
            "multigrow": "OK" if MULTIGROW_CONFIG["api_key"] else "NAO CONFIGURADO",
            "gtm": "OK" if GTM_CONFIG["container_id"] else "NAO CONFIGURADO",
            "ga4": "OK" if GA4_CONFIG["property_id"] else "NAO CONFIGURADO",
            "meta_ads": "OK" if META_CONFIG["access_token"] else "NAO CONFIGURADO",
            "ollama": "OK",  # Sempre disponivel localmente
        }

    else:
        result = {"erro": f"Ferramenta nao encontrada: {name}"}

    return [TextContent(
        type="text",
        text=json.dumps(result, ensure_ascii=False, indent=2)
    )]


# ==============================================================================
# MAIN
# ==============================================================================

async def main():
    """Inicia o servidor MCP Hub."""
    print("Iniciando Saldao Center MCP Hub...")
    print("Ferramentas disponiveis: Tiny ERP, Multigrow, GTM, GA4, Meta Ads, Copy IA")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
