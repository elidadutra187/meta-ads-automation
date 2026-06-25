# -*- coding: utf-8 -*-
"""
MCP local seguro para o Saldao Center.

Este servidor nao cria, ativa, pausa ou altera campanhas. Ele serve para
planejamento, copy, targeting, links e checagens locais antes da etapa online.
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from config.saldao_center import (
    DIFERENCIAIS,
    EMPRESA,
    GATILHOS,
    INTERESSES,
    PRODUTOS,
    TARGETING_PRINCIPAL,
)
from config.settings import META_CONFIG, OLLAMA_CONFIG, PATHS
from templates.prompts_saldao import HEADLINES_PRONTOS, TEXTOS_PRONTOS
from src.meta_online import (
    MetaOnlineError,
    alterar_budget_adset_meta,
    alterar_status_campanha_meta,
    criar_campanha_meta_pausada,
    listar_campanhas_meta,
    listar_contas_meta_ads,
    meta_online_status,
)
from src.audit_log import DB_PATH, audit_event, list_audit_logs
from src.company_store import (
    list_companies,
    list_company_connections,
    upsert_company,
    upsert_company_connection,
)
from src.secret_vault import load_secret_metadata, save_company_secret
from src.tiny_erp import (
    TinyERPError,
    tiny_consultar_estoque,
    tiny_listar_clientes,
    tiny_listar_pedidos,
    tiny_listar_produtos,
    tiny_obter_pedido,
    tiny_status,
)

server = Server("saldao-local-safe")
BASE_DIR = Path(__file__).resolve().parent.parent
MULTIGROW_EVENTS_PATH = BASE_DIR / "logs" / "multigrow_events.jsonl"
COMPOSIO_API_BASE = "https://backend.composio.dev/api/v3"
GOOGLE_SERVICES = {
    "google_analytics": {
        "nome": "Google Analytics 4",
        "env": ["GA4_PROPERTY_ID", "GA4_MEASUREMENT_ID"],
        "acoes_bloqueadas": ["alterar propriedade", "criar evento online", "excluir conversao"],
    },
    "googleads": {
        "nome": "Google Ads",
        "env": ["GOOGLE_ADS_CUSTOMER_ID", "GOOGLE_ADS_CONVERSION_ID"],
        "acoes_bloqueadas": ["criar campanha", "alterar budget", "ativar anuncio", "pausar campanha real"],
    },
    "google_search_console": {
        "nome": "Google Search Console",
        "env": [],
        "acoes_bloqueadas": ["enviar sitemap", "alterar propriedade"],
    },
    "googlebigquery": {
        "nome": "Google BigQuery",
        "env": [],
        "acoes_bloqueadas": ["criar dataset", "rodar consulta paga", "alterar tabela"],
    },
    "google_tag_manager": {
        "nome": "Google Tag Manager",
        "env": ["GTM_CONTAINER_ID", "GTM_ACCOUNT_ID"],
        "acoes_bloqueadas": ["publicar container", "criar tag online", "alterar trigger real"],
    },
}
SENSITIVE_ARGUMENT_KEYS = {
    "token",
    "api_key",
    "secret",
    "access_token",
    "app_secret",
    "password",
    "senha",
    "value",
}


def as_text(payload: dict) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


def mask_sensitive_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    masked = {}
    for key, value in (arguments or {}).items():
        key_lower = key.lower()
        if any(part in key_lower for part in SENSITIVE_ARGUMENT_KEYS):
            masked[key] = "***"
        else:
            masked[key] = value
    return masked


def is_real_value(value: str | None) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    placeholders = ("xxx", "xxxx", "placeholder", "seu_", "sua_", "123-456-7890", "aw-123456789")
    return bool(normalized) and not normalized.startswith(placeholders)


def get_google_env_status() -> dict:
    status = {}
    for slug, service in GOOGLE_SERVICES.items():
        status[slug] = {
            "nome": service["nome"],
            "variaveis": {
                key: {
                    "presente": bool(os.getenv(key)),
                    "parece_real": is_real_value(os.getenv(key)),
                }
                for key in service["env"]
            },
        }
    return status


def get_composio_google_status() -> dict:
    api_key = os.getenv("COMPOSIO_API_KEY", "").strip()
    if not api_key:
        return {
            "disponivel": False,
            "motivo": "COMPOSIO_API_KEY ausente no .env",
            "contas": {},
        }

    headers = {"x-api-key": api_key, "Content-Type": "application/json"}
    try:
        response = httpx.get(f"{COMPOSIO_API_BASE}/connected_accounts", headers=headers, timeout=20)
        response.raise_for_status()
    except Exception as exc:
        return {
            "disponivel": False,
            "motivo": f"Falha ao consultar Composio: {type(exc).__name__}",
            "contas": {},
        }

    data = response.json()
    items = data.get("items") or data.get("data") or []
    accounts = {}
    for item in items:
        toolkit = item.get("toolkit", {})
        slug = toolkit.get("slug") or item.get("toolkit_slug") or toolkit.get("name")
        if slug not in GOOGLE_SERVICES:
            continue
        accounts[slug] = {
            "nome": GOOGLE_SERVICES[slug]["nome"],
            "status": item.get("status", "desconhecido"),
            "id_mascarado": str(item.get("id") or item.get("uuid") or "")[:10] + "...",
        }
    return {
        "disponivel": True,
        "contas": accounts,
    }


def google_local_status() -> dict:
    composio = get_composio_google_status()
    env_status = get_google_env_status()
    resumo = {}
    for slug, service in GOOGLE_SERVICES.items():
        conta = composio.get("contas", {}).get(slug, {})
        variaveis = env_status[slug]["variaveis"]
        resumo[slug] = {
            "nome": service["nome"],
            "conexao": conta.get("status", "nao_encontrada"),
            "config_local_ok": all(v["parece_real"] for v in variaveis.values()) if variaveis else True,
            "modo": "LOCAL_SEGURO",
        }
    return {
        "modo": "GOOGLE_LOCAL_SEGURO",
        "observacao": "Consulta e planejamento local. Nenhuma alteracao online e executada por este MCP.",
        "composio_disponivel": composio.get("disponivel", False),
        "servicos": resumo,
    }


def diagnostico_google_local() -> dict:
    composio = get_composio_google_status()
    env_status = get_google_env_status()
    pendencias = []
    for slug, service in GOOGLE_SERVICES.items():
        conta = composio.get("contas", {}).get(slug)
        if not conta:
            pendencias.append(f"{service['nome']}: sem conta ativa encontrada no Composio/local.")
        elif conta.get("status") != "ACTIVE":
            pendencias.append(f"{service['nome']}: status {conta.get('status')}. Reautorizar antes de uso online.")

        for key, info in env_status[slug]["variaveis"].items():
            if not info["parece_real"]:
                pendencias.append(f"{service['nome']}: preencher {key} real no .env.")

    return {
        "modo": "DIAGNOSTICO_LOCAL",
        "servicos": google_local_status()["servicos"],
        "env": env_status,
        "pendencias": pendencias,
        "acoes_online_bloqueadas": [
            "publicar tags no GTM",
            "alterar campanhas Google Ads",
            "criar conversoes reais",
            "rodar consultas BigQuery pagas",
            "alterar propriedades GA4/Search Console",
        ],
    }


def planejar_google_ads_local(produto: str, objetivo: str, budget_diario: int) -> dict:
    return {
        "modo": "PLANO_GOOGLE_ADS_LOCAL_SEM_PUBLICAR",
        "produto": produto,
        "objetivo": objetivo,
        "budget_diario_centavos": budget_diario,
        "budget_diario_reais": round(budget_diario / 100, 2),
        "estrutura_sugerida": {
            "campanha": f"Search - {produto} - Baixada Santista",
            "grupos": [
                f"{produto} preco",
                f"{produto} promocao",
                f"{produto} instalacao",
            ],
            "conversao": "WhatsApp ou formulario, validar antes no GTM/GA4",
        },
        "palavras_chave_iniciais": [
            f"{produto} em santos",
            f"{produto} baixada santista",
            f"comprar {produto}",
            f"{produto} promocao",
        ],
        "nao_executado": "Nenhuma campanha foi criada ou alterada no Google Ads.",
    }


def plano_google_analytics_local() -> dict:
    return {
        "modo": "PLANO_GA4_GTM_LOCAL_SEM_PUBLICAR",
        "eventos_recomendados": [
            "whatsapp_click",
            "lead_form_submit",
            "phone_click",
            "view_product_category",
            "quote_request",
        ],
        "checklist": [
            "confirmar GA4_PROPERTY_ID e GA4_MEASUREMENT_ID reais",
            "confirmar GTM_CONTAINER_ID e GTM_ACCOUNT_ID reais",
            "testar eventos no preview do GTM antes de publicar",
            "marcar conversoes no GA4 somente depois de validar recebimento",
        ],
        "nao_executado": "Nenhum container, tag ou evento foi publicado.",
    }


def read_multigrow_events(limit: int = 20) -> list[dict]:
    if not MULTIGROW_EVENTS_PATH.exists():
        return []
    lines = MULTIGROW_EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def local_status() -> dict:
    required_meta = ["app_id", "app_secret", "access_token", "ad_account_id", "page_id"]
    try:
        empresas = list_companies(include_inactive=True)
    except Exception:
        empresas = []
    return {
        "modo": "SAFE_LOCAL",
        "multiempresa": {
            "ativo": True,
            "empresas_cadastradas": len(empresas),
            "company_ids": [empresa["company_id"] for empresa in empresas],
            "sqlite_local": str(DB_PATH),
        },
        "cofre": {
            "tipo": "LOCAL_FILE_VAULT_IGNORADO_PELO_GIT",
            "valores_expostos": False,
            "destino_online_recomendado": "Supabase Vault, Render/Railway secrets ou AWS Secrets Manager",
        },
        "acoes_online_bloqueadas": [
            "criar_campanha",
            "ativar_campanha",
            "pausar_campanha",
            "alterar_budget",
            "upload_criativos_meta",
        ],
        "env_meta": {
            key: bool(META_CONFIG.get(key)) and not str(META_CONFIG.get(key)).startswith("seu_")
            for key in required_meta
        },
        "google_local": google_local_status()["servicos"],
        "ollama_model": OLLAMA_CONFIG["model"],
        "criativos_path": str(PATHS["criativos"]),
    }


def gerar_copy_local(produto: str, diferencial: str, publico: str) -> dict:
    headline_base = f"{produto} em Oferta"
    if len(headline_base) > 40:
        headline_base = headline_base[:37].rstrip() + "..."

    texto = f"{produto} com {diferencial}. Chame no WhatsApp e peca seu orcamento."
    if len(texto) > 125:
        texto = texto[:122].rstrip() + "..."

    return {
        "headline": headline_base,
        "texto_principal": texto,
        "descricao": "Chama no WhatsApp",
        "publico": publico,
        "observacao": "Copy local segura, sem chamada a API externa.",
    }


def montar_plano_campanha(produto: str, diferencial: str, budget_diario: int) -> dict:
    return {
        "modo": "PLANO_SEM_PUBLICAR",
        "produto": produto,
        "objetivo_recomendado": "Conversas no WhatsApp",
        "diferencial": diferencial,
        "budget_diario_centavos": budget_diario,
        "budget_diario_reais": round(budget_diario / 100, 2),
        "targeting": TARGETING_PRINCIPAL,
        "copy_sugerido": gerar_copy_local(produto, diferencial, "Baixada Santista"),
        "checklist_antes_online": [
            "confirmar credenciais Meta reais no .env",
            "validar criativos aprovados para anuncio",
            "conferir URL ou WhatsApp de destino",
            "rodar primeiro em PAUSED",
            "revisar manualmente no Gerenciador de Anuncios antes de ativar",
        ],
    }


def editar_copy_local(
    headline: str,
    texto: str,
    objetivo: str,
    tom: str,
    limite_texto: int,
) -> dict:
    objetivo_lower = objetivo.lower()
    tom_lower = tom.lower()

    nova_headline = headline.strip()
    novo_texto = texto.strip()

    if "whatsapp" in objetivo_lower and "whatsapp" not in novo_texto.lower():
        novo_texto = f"{novo_texto} Chame no WhatsApp."

    if "urg" in tom_lower and not any(p in novo_texto.lower() for p in ["agora", "hoje", "limitado"]):
        novo_texto = f"{novo_texto} Estoque limitado."

    if "econom" in tom_lower and not any(p in novo_texto.lower() for p in ["preco", "oferta", "desconto"]):
        nova_headline = "Oferta " + nova_headline

    if len(nova_headline) > 40:
        nova_headline = nova_headline[:37].rstrip() + "..."

    if len(novo_texto) > limite_texto:
        novo_texto = novo_texto[: max(0, limite_texto - 3)].rstrip() + "..."

    return {
        "headline_original": headline,
        "texto_original": texto,
        "headline_editada": nova_headline,
        "texto_editado": novo_texto,
        "objetivo": objetivo,
        "tom": tom,
        "status": "editado_localmente_sem_publicar",
    }


def criar_teste_ab_local(produto: str, diferencial: str, publico: str) -> dict:
    base = gerar_copy_local(produto, diferencial, publico)
    return {
        "modo": "TESTE_AB_LOCAL_SEM_PUBLICAR",
        "produto": produto,
        "variacoes": [
            {
                "nome": "A - Urgencia",
                "headline": f"{produto} Hoje",
                "texto": f"{produto} com {diferencial}. Estoque limitado. Chame no WhatsApp.",
                "hipotese": "urgencia aumenta conversas qualificadas",
            },
            {
                "nome": "B - Economia",
                "headline": f"Oferta em {produto}",
                "texto": f"Economize na reforma: {produto} com {diferencial}. Peca orcamento no WhatsApp.",
                "hipotese": "preco e parcelamento reduzem friccao",
            },
            {
                "nome": "C - Facilidade",
                "headline": "Reforma Sem Complicar",
                "texto": f"Calculamos seu {produto} e enviamos orcamento pelo WhatsApp. {diferencial}.",
                "hipotese": "facilidade de atendimento aumenta leads",
            },
        ],
        "copy_base": base,
        "metricas_para_decisao": [
            "custo por conversa",
            "conversas iniciadas",
            "CTR",
            "frequencia",
        ],
    }


def duplicar_plano_local(nome_base: str, novo_publico: str, novo_budget: int) -> dict:
    return {
        "modo": "DUPLICACAO_LOCAL_SEM_PUBLICAR",
        "campanha_base": nome_base,
        "nova_campanha_sugerida": f"{nome_base} - {novo_publico}",
        "novo_publico": novo_publico,
        "novo_budget_centavos": novo_budget,
        "novo_budget_reais": round(novo_budget / 100, 2),
        "alteracoes_recomendadas": [
            "manter campanha original pausada ou sem alteracao ate revisar",
            "criar duplicata primeiro em PAUSED quando passar para online",
            "trocar apenas publico ou criativo por teste para isolar aprendizado",
        ],
    }


def rotina_marketing_local() -> dict:
    return {
        "modo": "OPERACIONAL_LOCAL",
        "diario": [
            "revisar campanhas com maior gasto",
            "identificar copies com CTR baixo",
            "montar 3 novas variacoes para produtos prioritarios",
            "separar criativos aprovados para teste",
        ],
        "semanal": [
            "comparar custo por conversa por campanha",
            "duplicar vencedoras para novo publico",
            "pausar manualmente perdedoras somente apos revisao",
            "criar backlog de ofertas para a semana seguinte",
        ],
        "nao_executa_neste_mcp": [
            "publicar campanha",
            "ativar campanha",
            "pausar campanha real",
            "alterar budget real",
        ],
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="cadastrar_empresa",
            description="Cria ou atualiza uma empresa no cadastro multiempresa local.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {"type": "string"},
                    "meta_ad_account_id": {"type": "string"},
                    "meta_pixel_id": {"type": "string"},
                    "facebook_page_id": {"type": "string"},
                    "instagram_account_id": {"type": "string"},
                    "whatsapp": {"type": "string"},
                    "crm_name": {"type": "string"},
                    "erp_name": {"type": "string"},
                    "google_sheet_id": {"type": "string"},
                    "ga4_property_id": {"type": "string"},
                    "gtm_container_id": {"type": "string"},
                },
            },
        ),
        Tool(
            name="listar_empresas",
            description="Lista empresas cadastradas no MCP local.",
            inputSchema={
                "type": "object",
                "properties": {"include_inactive": {"type": "boolean"}},
            },
        ),
        Tool(
            name="registrar_conexao_empresa",
            description="Registra o status de uma conexao por empresa, como metaads, tiny, multigrow, google_sheets ou composio.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "service": {"type": "string"},
                    "status": {"type": "string"},
                    "external_account_id": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["company_id", "service"],
            },
        ),
        Tool(
            name="listar_conexoes_empresa",
            description="Lista conexoes cadastradas para uma empresa.",
            inputSchema={
                "type": "object",
                "properties": {"company_id": {"type": "string"}},
                "required": ["company_id"],
            },
        ),
        Tool(
            name="salvar_segredo_empresa",
            description="Salva token/chave de uma empresa em cofre local ignorado pelo git e retorna apenas mascara/fingerprint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "service": {"type": "string"},
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["company_id", "service", "key", "value"],
            },
        ),
        Tool(
            name="status_cofre_empresa",
            description="Mostra quais segredos existem para a empresa sem expor valores.",
            inputSchema={
                "type": "object",
                "properties": {"company_id": {"type": "string"}},
                "required": ["company_id"],
            },
        ),
        Tool(
            name="listar_auditoria_mcp",
            description="Lista logs de auditoria do MCP local, opcionalmente filtrando por empresa.",
            inputSchema={
                "type": "object",
                "properties": {
                    "company_id": {"type": "string"},
                    "limite": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="status_seguro",
            description="Mostra o status local e confirma que acoes online estao bloqueadas.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="listar_produtos",
            description="Lista produtos principais do Saldao Center.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="listar_diferenciais",
            description="Lista diferenciais, gatilhos e interesses para campanhas.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="obter_targeting",
            description="Retorna targeting recomendado para Baixada Santista.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="gerar_copy_segura",
            description="Gera copy local sem publicar campanha e sem chamar APIs externas.",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto": {"type": "string"},
                    "diferencial": {"type": "string"},
                    "publico": {"type": "string"},
                },
                "required": ["produto"],
            },
        ),
        Tool(
            name="montar_plano_campanha",
            description="Monta um plano de campanha seguro, sem criar nada no Meta Ads.",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto": {"type": "string"},
                    "diferencial": {"type": "string"},
                    "budget_diario": {"type": "integer", "description": "Budget em centavos."},
                },
                "required": ["produto"],
            },
        ),
        Tool(
            name="editar_copy",
            description="Edita uma copy localmente para WhatsApp, urgencia, economia ou facilidade.",
            inputSchema={
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "texto": {"type": "string"},
                    "objetivo": {"type": "string"},
                    "tom": {"type": "string"},
                    "limite_texto": {"type": "integer"},
                },
                "required": ["headline", "texto"],
            },
        ),
        Tool(
            name="criar_teste_ab",
            description="Cria um teste A/B local com 3 variacoes e hipoteses, sem publicar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto": {"type": "string"},
                    "diferencial": {"type": "string"},
                    "publico": {"type": "string"},
                },
                "required": ["produto"],
            },
        ),
        Tool(
            name="duplicar_plano_campanha",
            description="Prepara uma duplicacao local de campanha com novo publico ou budget, sem publicar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nome_base": {"type": "string"},
                    "novo_publico": {"type": "string"},
                    "novo_budget": {"type": "integer"},
                },
                "required": ["nome_base", "novo_publico"],
            },
        ),
        Tool(
            name="rotina_marketing_operacional",
            description="Gera a rotina operacional de marketing para uso diario e semanal.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="sugerir_headlines",
            description="Retorna headlines e textos prontos para revisao.",
            inputSchema={
                "type": "object",
                "properties": {"quantidade": {"type": "integer"}},
            },
        ),
        Tool(
            name="montar_link_whatsapp",
            description="Monta link WhatsApp com mensagem pre-definida.",
            inputSchema={
                "type": "object",
                "properties": {"mensagem": {"type": "string"}},
            },
        ),
        Tool(
            name="calcular_metragem",
            description="Calcula area de piso com margem de seguranca.",
            inputSchema={
                "type": "object",
                "properties": {
                    "largura": {"type": "number"},
                    "comprimento": {"type": "number"},
                    "margem": {"type": "number"},
                },
                "required": ["largura", "comprimento"],
            },
        ),
        Tool(
            name="bloquear_acao_online",
            description="Explica por que uma acao online foi bloqueada no MCP seguro.",
            inputSchema={
                "type": "object",
                "properties": {"acao": {"type": "string"}},
                "required": ["acao"],
            },
        ),
        Tool(
            name="listar_eventos_multigrow",
            description="Lista eventos recentes recebidos do webhook da Multigrow.",
            inputSchema={
                "type": "object",
                "properties": {"limite": {"type": "integer"}},
            },
        ),
        Tool(
            name="resumo_multigrow",
            description="Resume eventos recentes recebidos do webhook da Multigrow.",
            inputSchema={
                "type": "object",
                "properties": {"limite": {"type": "integer"}},
            },
        ),
        Tool(
            name="status_google_local",
            description="Mostra status local seguro das conexoes Google no MCP local.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="diagnostico_google_local",
            description="Diagnostica Google Ads, GA4, GTM, Search Console e BigQuery no modo local seguro.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="planejar_google_ads_local",
            description="Monta plano local de Google Ads sem criar ou alterar campanha real.",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto": {"type": "string"},
                    "objetivo": {"type": "string"},
                    "budget_diario": {"type": "integer", "description": "Budget em centavos."},
                },
                "required": ["produto"],
            },
        ),
        Tool(
            name="plano_google_analytics_local",
            description="Monta plano local de eventos GA4/GTM sem publicar tags.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="bloquear_acao_google_online",
            description="Explica o bloqueio de uma acao online do Google no MCP local.",
            inputSchema={
                "type": "object",
                "properties": {"acao": {"type": "string"}},
                "required": ["acao"],
            },
        ),
        Tool(
            name="status_meta_online",
            description="Mostra se o Meta/Facebook no Composio esta pronto para alteracoes reais.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="listar_contas_meta_ads_online",
            description="Lista contas de anuncio Meta disponiveis pela conexao ativa do Composio.",
            inputSchema={
                "type": "object",
                "properties": {"limite": {"type": "integer"}},
            },
        ),
        Tool(
            name="listar_campanhas_meta_online",
            description="Lista campanhas Meta Ads de uma conta de anuncio.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_account_id": {"type": "string"},
                    "limite": {"type": "integer"},
                    "status": {"type": "string"},
                },
                "required": ["ad_account_id"],
            },
        ),
        Tool(
            name="alterar_status_campanha_meta_online",
            description="Altera de verdade o status de uma campanha Meta, com dry-run e codigo de confirmacao.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_id": {"type": "string"},
                    "novo_status": {"type": "string", "enum": ["PAUSED", "ACTIVE"]},
                    "confirmar": {"type": "boolean"},
                    "codigo_confirmacao": {"type": "string"},
                },
                "required": ["campaign_id", "novo_status"],
            },
        ),
        Tool(
            name="alterar_budget_adset_meta_online",
            description="Altera de verdade o budget diario de um conjunto de anuncios Meta, com limite local e confirmacao.",
            inputSchema={
                "type": "object",
                "properties": {
                    "adset_id": {"type": "string"},
                    "budget_diario_centavos": {"type": "integer"},
                    "confirmar": {"type": "boolean"},
                    "codigo_confirmacao": {"type": "string"},
                },
                "required": ["adset_id", "budget_diario_centavos"],
            },
        ),
        Tool(
            name="criar_campanha_meta_pausada_online",
            description="Cria uma campanha Meta real sempre em PAUSED, com dry-run e codigo de confirmacao.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ad_account_id": {"type": "string"},
                    "nome": {"type": "string"},
                    "objetivo": {"type": "string"},
                    "confirmar": {"type": "boolean"},
                    "codigo_confirmacao": {"type": "string"},
                },
                "required": ["ad_account_id", "nome"],
            },
        ),
        Tool(
            name="status_erp_tiny",
            description="Verifica se o Tiny ERP esta conectado pelo token local.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="tiny_listar_produtos",
            description="Lista produtos do Tiny ERP em modo leitura.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pagina": {"type": "integer"},
                    "pesquisa": {"type": "string"},
                },
            },
        ),
        Tool(
            name="tiny_consultar_estoque",
            description="Consulta estoque de um produto do Tiny ERP por ID.",
            inputSchema={
                "type": "object",
                "properties": {"produto_id": {"type": "string"}},
                "required": ["produto_id"],
            },
        ),
        Tool(
            name="tiny_listar_pedidos",
            description="Lista pedidos do Tiny ERP em modo leitura.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pagina": {"type": "integer"},
                    "situacao": {"type": "string"},
                },
            },
        ),
        Tool(
            name="tiny_obter_pedido",
            description="Obtem detalhes de um pedido do Tiny ERP por ID.",
            inputSchema={
                "type": "object",
                "properties": {"pedido_id": {"type": "string"}},
                "required": ["pedido_id"],
            },
        ),
        Tool(
            name="tiny_listar_clientes",
            description="Lista clientes/contatos do Tiny ERP em modo leitura.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pagina": {"type": "integer"},
                    "pesquisa": {"type": "string"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    arguments = arguments or {}
    company_id_for_log = arguments.get("company_id")
    try:
        audit_event(
            tool=name,
            action="call_tool",
            company_id=company_id_for_log,
            target=arguments.get("campaign_id") or arguments.get("adset_id") or arguments.get("service"),
            metadata={"arguments": mask_sensitive_arguments(arguments)},
            status="received",
        )
    except Exception:
        pass

    try:
        if name == "cadastrar_empresa":
            return as_text({
                "empresa": upsert_company(arguments),
                "modo": "MULTIEMPRESA_LOCAL",
            })

        if name == "listar_empresas":
            return as_text({
                "empresas": list_companies(arguments.get("include_inactive", False)),
                "modo": "MULTIEMPRESA_LOCAL",
            })

        if name == "registrar_conexao_empresa":
            return as_text({
                "conexao": upsert_company_connection(
                    arguments["company_id"],
                    arguments["service"],
                    arguments.get("status", "pending"),
                    arguments.get("external_account_id", ""),
                    arguments.get("notes", ""),
                )
            })

        if name == "listar_conexoes_empresa":
            return as_text({
                "company_id": arguments["company_id"],
                "conexoes": list_company_connections(arguments["company_id"]),
            })

        if name == "salvar_segredo_empresa":
            return as_text(save_company_secret(
                arguments["company_id"],
                arguments["service"],
                arguments["key"],
                arguments["value"],
            ))

        if name == "status_cofre_empresa":
            return as_text(load_secret_metadata(arguments["company_id"]))

        if name == "listar_auditoria_mcp":
            return as_text({
                "auditoria": list_audit_logs(
                    arguments.get("company_id"),
                    arguments.get("limite", 50),
                )
            })
    except (ValueError, RuntimeError) as exc:
        return as_text({
            "erro": type(exc).__name__,
            "mensagem": str(exc),
            "alterado": False,
        })

    if name == "status_seguro":
        return as_text(local_status())

    if name == "listar_produtos":
        return as_text({"produtos": PRODUTOS})

    if name == "listar_diferenciais":
        return as_text({"diferenciais": DIFERENCIAIS, "gatilhos": GATILHOS, "interesses": INTERESSES})

    if name == "obter_targeting":
        return as_text(TARGETING_PRINCIPAL)

    if name == "gerar_copy_segura":
        return as_text(gerar_copy_local(
            arguments["produto"],
            arguments.get("diferencial", "15x sem juros"),
            arguments.get("publico", "Baixada Santista"),
        ))

    if name == "montar_plano_campanha":
        return as_text(montar_plano_campanha(
            arguments["produto"],
            arguments.get("diferencial", "15x sem juros"),
            arguments.get("budget_diario", 5000),
        ))

    if name == "editar_copy":
        return as_text(editar_copy_local(
            arguments["headline"],
            arguments["texto"],
            arguments.get("objetivo", "conversas no WhatsApp"),
            arguments.get("tom", "direto"),
            arguments.get("limite_texto", 125),
        ))

    if name == "criar_teste_ab":
        return as_text(criar_teste_ab_local(
            arguments["produto"],
            arguments.get("diferencial", "15x sem juros"),
            arguments.get("publico", "Baixada Santista"),
        ))

    if name == "duplicar_plano_campanha":
        return as_text(duplicar_plano_local(
            arguments["nome_base"],
            arguments["novo_publico"],
            arguments.get("novo_budget", 5000),
        ))

    if name == "rotina_marketing_operacional":
        return as_text(rotina_marketing_local())

    if name == "sugerir_headlines":
        qtd = arguments.get("quantidade", 5)
        return as_text({"headlines": HEADLINES_PRONTOS[:qtd], "textos": TEXTOS_PRONTOS[:qtd]})

    if name == "montar_link_whatsapp":
        msg = arguments.get("mensagem", "Ola, vi o anuncio e quero saber mais!")
        return as_text({
            "link": f"https://wa.me/{EMPRESA['whatsapp']}?text={quote(msg)}",
            "whatsapp": EMPRESA["whatsapp_display"],
            "mensagem": msg,
        })

    if name == "calcular_metragem":
        area = arguments["largura"] * arguments["comprimento"]
        margem = arguments.get("margem", 10)
        return as_text({
            "area_m2": round(area, 2),
            "area_com_margem_m2": round(area * (1 + margem / 100), 2),
            "margem_percentual": margem,
        })

    if name == "bloquear_acao_online":
        return as_text({
            "bloqueado": True,
            "acao": arguments["acao"],
            "motivo": "O MCP local seguro nao executa alteracoes online. Use apenas para planejar e revisar.",
            "proxima_etapa": "Depois de validado localmente, criar um MCP online separado com dry-run e aprovacao explicita.",
        })

    if name == "listar_eventos_multigrow":
        return as_text({"eventos": read_multigrow_events(arguments.get("limite", 20))})

    if name == "resumo_multigrow":
        eventos = read_multigrow_events(arguments.get("limite", 50))
        tipos = {}
        for evento in eventos:
            payload = evento.get("payload", {})
            tipo = payload.get("event") or payload.get("evento") or payload.get("type") or payload.get("tipo") or "desconhecido"
            tipos[str(tipo)] = tipos.get(str(tipo), 0) + 1
        return as_text({
            "total_eventos": len(eventos),
            "por_tipo": tipos,
            "ultimo_evento": eventos[-1] if eventos else None,
        })

    if name == "status_google_local":
        return as_text(google_local_status())

    if name == "diagnostico_google_local":
        return as_text(diagnostico_google_local())

    if name == "planejar_google_ads_local":
        return as_text(planejar_google_ads_local(
            arguments["produto"],
            arguments.get("objetivo", "gerar conversas no WhatsApp"),
            arguments.get("budget_diario", 5000),
        ))

    if name == "plano_google_analytics_local":
        return as_text(plano_google_analytics_local())

    if name == "bloquear_acao_google_online":
        return as_text({
            "bloqueado": True,
            "acao": arguments["acao"],
            "motivo": "O MCP local seguro centraliza Google primeiro, mas nao executa alteracoes online.",
            "proxima_etapa": "Validar plano local; depois criar MCP online separado com dry-run, auditoria e aprovacao explicita.",
        })

    try:
        if name == "status_meta_online":
            return as_text(meta_online_status())

        if name == "listar_contas_meta_ads_online":
            return as_text(listar_contas_meta_ads(arguments.get("limite", 25)))

        if name == "listar_campanhas_meta_online":
            return as_text(listar_campanhas_meta(
                arguments["ad_account_id"],
                arguments.get("limite", 25),
                arguments.get("status", ""),
            ))

        if name == "alterar_status_campanha_meta_online":
            return as_text(alterar_status_campanha_meta(
                arguments["campaign_id"],
                arguments["novo_status"],
                arguments.get("confirmar", False),
                arguments.get("codigo_confirmacao", ""),
            ))

        if name == "alterar_budget_adset_meta_online":
            return as_text(alterar_budget_adset_meta(
                arguments["adset_id"],
                arguments["budget_diario_centavos"],
                arguments.get("confirmar", False),
                arguments.get("codigo_confirmacao", ""),
            ))

        if name == "criar_campanha_meta_pausada_online":
            return as_text(criar_campanha_meta_pausada(
                arguments["ad_account_id"],
                arguments["nome"],
                arguments.get("objetivo", "OUTCOME_LEADS"),
                arguments.get("confirmar", False),
                arguments.get("codigo_confirmacao", ""),
            ))
    except (MetaOnlineError, httpx.HTTPError) as exc:
        return as_text({
            "erro": type(exc).__name__,
            "mensagem": str(exc),
            "alterado": False,
        })

    try:
        if name == "status_erp_tiny":
            return as_text(tiny_status())

        if name == "tiny_listar_produtos":
            return as_text(tiny_listar_produtos(
                arguments.get("pagina", 1),
                arguments.get("pesquisa", ""),
            ))

        if name == "tiny_consultar_estoque":
            return as_text(tiny_consultar_estoque(arguments["produto_id"]))

        if name == "tiny_listar_pedidos":
            return as_text(tiny_listar_pedidos(
                arguments.get("pagina", 1),
                arguments.get("situacao", ""),
            ))

        if name == "tiny_obter_pedido":
            return as_text(tiny_obter_pedido(arguments["pedido_id"]))

        if name == "tiny_listar_clientes":
            return as_text(tiny_listar_clientes(
                arguments.get("pagina", 1),
                arguments.get("pesquisa", ""),
            ))
    except (TinyERPError, httpx.HTTPError) as exc:
        return as_text({
            "erro": type(exc).__name__,
            "mensagem": str(exc),
            "alterado": False,
        })

    return as_text({"erro": f"Ferramenta nao encontrada: {name}"})


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
