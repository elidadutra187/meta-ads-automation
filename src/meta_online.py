# -*- coding: utf-8 -*-
"""
Operacoes online protegidas para Meta/Graph via Composio.

As credenciais ficam no Composio. Este modulo chama o proxy execute, que injeta
a autenticacao do connected account sem expor tokens localmente.
"""
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from src.audit_log import audit_event

load_dotenv()
COMPOSIO_API_BASE = "https://backend.composio.dev/api/v3.1"
COMPOSIO_ACCOUNTS_BASE = "https://backend.composio.dev/api/v3"
META_TOOLKITS = {"metaads", "facebook"}
MAX_DAILY_BUDGET_CENTS = int(os.getenv("META_ONLINE_MAX_DAILY_BUDGET_CENTS", "10000"))


class MetaOnlineError(RuntimeError):
    pass


def _api_key() -> str:
    value = os.getenv("COMPOSIO_API_KEY", "").strip()
    if not value:
        raise MetaOnlineError("COMPOSIO_API_KEY ausente no .env.")
    return value


def _headers() -> dict[str, str]:
    return {"x-api-key": _api_key(), "Content-Type": "application/json"}


def _mask(value: str) -> str:
    if not value:
        return ""
    return value[:10] + "..."


def _normalize_ad_account_id(ad_account_id: str) -> str:
    clean = str(ad_account_id or "").strip()
    if not clean:
        raise MetaOnlineError("Informe ad_account_id.")
    return clean if clean.startswith("act_") else f"act_{clean}"


def list_meta_connections() -> dict:
    response = httpx.get(
        f"{COMPOSIO_ACCOUNTS_BASE}/connected_accounts",
        headers=_headers(),
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    items = data.get("items") or data.get("data") or []
    connections = []
    for item in items:
        toolkit = item.get("toolkit", {})
        slug = toolkit.get("slug") or item.get("toolkit_slug") or toolkit.get("name")
        if slug not in META_TOOLKITS:
            continue
        connections.append(
            {
                "toolkit": slug,
                "status": item.get("status", "desconhecido"),
                "id": item.get("id") or item.get("uuid"),
                "id_mascarado": _mask(str(item.get("id") or item.get("uuid") or "")),
            }
        )
    return {"connections": connections}


def get_active_meta_connection() -> dict:
    connections = list_meta_connections()["connections"]
    for preferred in ("metaads", "facebook"):
        for connection in connections:
            if connection["toolkit"] == preferred and connection["status"] == "ACTIVE":
                return connection
    raise MetaOnlineError(
        "Nenhuma conexao Meta Ads/Facebook ACTIVE no Composio. Reautorize metaads antes de executar online."
    )


def proxy_execute(
    method: str,
    endpoint: str,
    connected_account_id: str | None = None,
    parameters: list[dict[str, Any]] | None = None,
    body: dict[str, Any] | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "method": method.upper(),
        "endpoint": endpoint,
    }
    if connected_account_id:
        payload["connected_account_id"] = connected_account_id
    if parameters:
        payload["parameters"] = parameters
    if body:
        payload["body"] = body

    response = httpx.post(
        f"{COMPOSIO_API_BASE}/tools/execute/proxy",
        headers=_headers(),
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    return response.json()


def meta_online_status() -> dict:
    try:
        connections = list_meta_connections()["connections"]
    except Exception as exc:
        return {
            "pronto_para_alterar": False,
            "erro": f"{type(exc).__name__}: {exc}",
            "connections": [],
        }
    active = [c for c in connections if c["status"] == "ACTIVE"]
    active_metaads = [c for c in active if c["toolkit"] == "metaads"]
    active_facebook = [c for c in active if c["toolkit"] == "facebook"]
    return {
        "modo": "ONLINE_PROTEGIDO",
        "conexao_meta_facebook_ativa": bool(active),
        "pronto_para_alterar_ads": bool(active_metaads),
        "observacao": (
            "metaads ACTIVE e o caminho recomendado para alterar campanhas. "
            "facebook ACTIVE pode falhar em Ads se nao tiver permissoes ads_read/ads_management."
        ),
        "connections": [
            {k: v for k, v in item.items() if k != "id"}
            for item in connections
        ],
        "active_fallback_facebook": bool(active_facebook),
        "preferencia_execucao": "metaads ACTIVE; fallback facebook ACTIVE se tiver escopos suficientes",
        "limite_budget_diario_centavos": MAX_DAILY_BUDGET_CENTS,
        "confirmacao_obrigatoria": True,
    }


def confirmation_code(action: str, object_id: str, value: str) -> str:
    return f"CONFIRMAR_META::{action}::{object_id}::{value}"


def ensure_confirmed(action: str, object_id: str, value: str, confirmar: bool, codigo_confirmacao: str) -> None:
    expected = confirmation_code(action, object_id, value)
    if not confirmar or codigo_confirmacao != expected:
        raise MetaOnlineError(f"Confirmacao obrigatoria. Reenvie com codigo_confirmacao='{expected}'.")


def listar_contas_meta_ads(limite: int = 25) -> dict:
    connection = get_active_meta_connection()
    result = proxy_execute(
        "GET",
        "/me/adaccounts",
        connected_account_id=connection["id"],
        parameters=[
            {"name": "fields", "value": "id,name,account_status,currency,timezone_name", "type": "query"},
            {"name": "limit", "value": str(limite), "type": "query"},
        ],
    )
    return {
        "modo": "ONLINE_READ",
        "connection": {k: v for k, v in connection.items() if k != "id"},
        "resultado": result.get("data", result),
    }


def listar_campanhas_meta(ad_account_id: str, limite: int = 25, status: str = "") -> dict:
    connection = get_active_meta_connection()
    params = [
        {"name": "fields", "value": "id,name,status,effective_status,objective,daily_budget,created_time,updated_time", "type": "query"},
        {"name": "limit", "value": str(limite), "type": "query"},
    ]
    if status:
        params.append({"name": "filtering", "value": f'[{{"field":"campaign.effective_status","operator":"IN","value":["{status}"]}}]', "type": "query"})

    result = proxy_execute(
        "GET",
        f"/{_normalize_ad_account_id(ad_account_id)}/campaigns",
        connected_account_id=connection["id"],
        parameters=params,
    )
    return {
        "modo": "ONLINE_READ",
        "connection": {k: v for k, v in connection.items() if k != "id"},
        "resultado": result.get("data", result),
    }


def alterar_status_campanha_meta(
    campaign_id: str,
    novo_status: str,
    confirmar: bool = False,
    codigo_confirmacao: str = "",
) -> dict:
    status = novo_status.upper().strip()
    if status not in {"PAUSED", "ACTIVE"}:
        raise MetaOnlineError("novo_status deve ser PAUSED ou ACTIVE.")

    expected = confirmation_code("STATUS_CAMPANHA", campaign_id, status)
    if not confirmar:
        payload = {
            "dry_run": True,
            "acao": "alterar_status_campanha",
            "campaign_id": campaign_id,
            "novo_status": status,
            "codigo_confirmacao_necessario": expected,
            "nada_foi_alterado": True,
        }
        audit_event(
            tool="meta_online",
            action="alterar_status_campanha_dry_run",
            target=campaign_id,
            after=payload,
            status="dry_run",
        )
        return payload
    ensure_confirmed("STATUS_CAMPANHA", campaign_id, status, confirmar, codigo_confirmacao)

    connection = get_active_meta_connection()
    result = proxy_execute(
        "POST",
        f"/{campaign_id}",
        connected_account_id=connection["id"],
        parameters=[{"name": "status", "value": status, "type": "query"}],
    )
    payload = {
        "dry_run": False,
        "alterado": True,
        "campaign_id": campaign_id,
        "novo_status": status,
        "resultado": result.get("data", result),
    }
    audit_event(
        tool="meta_online",
        action="alterar_status_campanha",
        target=campaign_id,
        after=payload,
        status="ok",
    )
    return payload


def alterar_budget_adset_meta(
    adset_id: str,
    budget_diario_centavos: int,
    confirmar: bool = False,
    codigo_confirmacao: str = "",
) -> dict:
    budget = int(budget_diario_centavos)
    if budget < 1000:
        raise MetaOnlineError("Budget minimo de seguranca: 1000 centavos.")
    if budget > MAX_DAILY_BUDGET_CENTS:
        raise MetaOnlineError(f"Budget acima do limite local: {MAX_DAILY_BUDGET_CENTS} centavos.")

    expected = confirmation_code("BUDGET_ADSET", adset_id, str(budget))
    if not confirmar:
        payload = {
            "dry_run": True,
            "acao": "alterar_budget_adset",
            "adset_id": adset_id,
            "budget_diario_centavos": budget,
            "codigo_confirmacao_necessario": expected,
            "nada_foi_alterado": True,
        }
        audit_event(
            tool="meta_online",
            action="alterar_budget_adset_dry_run",
            target=adset_id,
            after=payload,
            status="dry_run",
        )
        return payload
    ensure_confirmed("BUDGET_ADSET", adset_id, str(budget), confirmar, codigo_confirmacao)

    connection = get_active_meta_connection()
    result = proxy_execute(
        "POST",
        f"/{adset_id}",
        connected_account_id=connection["id"],
        parameters=[{"name": "daily_budget", "value": str(budget), "type": "query"}],
    )
    payload = {
        "dry_run": False,
        "alterado": True,
        "adset_id": adset_id,
        "budget_diario_centavos": budget,
        "resultado": result.get("data", result),
    }
    audit_event(
        tool="meta_online",
        action="alterar_budget_adset",
        target=adset_id,
        after=payload,
        status="ok",
    )
    return payload


def criar_campanha_meta_pausada(
    ad_account_id: str,
    nome: str,
    objetivo: str = "OUTCOME_LEADS",
    confirmar: bool = False,
    codigo_confirmacao: str = "",
) -> dict:
    objective = objetivo.upper().strip()
    expected = confirmation_code("CRIAR_CAMPANHA_PAUSADA", _normalize_ad_account_id(ad_account_id), nome)
    if not confirmar:
        payload = {
            "dry_run": True,
            "acao": "criar_campanha_meta_pausada",
            "ad_account_id": _normalize_ad_account_id(ad_account_id),
            "nome": nome,
            "objetivo": objective,
            "status": "PAUSED",
            "codigo_confirmacao_necessario": expected,
            "nada_foi_alterado": True,
        }
        audit_event(
            tool="meta_online",
            action="criar_campanha_meta_pausada_dry_run",
            target=_normalize_ad_account_id(ad_account_id),
            after=payload,
            status="dry_run",
        )
        return payload
    ensure_confirmed("CRIAR_CAMPANHA_PAUSADA", _normalize_ad_account_id(ad_account_id), nome, confirmar, codigo_confirmacao)

    connection = get_active_meta_connection()
    result = proxy_execute(
        "POST",
        f"/{_normalize_ad_account_id(ad_account_id)}/campaigns",
        connected_account_id=connection["id"],
        parameters=[
            {"name": "name", "value": nome, "type": "query"},
            {"name": "objective", "value": objective, "type": "query"},
            {"name": "status", "value": "PAUSED", "type": "query"},
            {"name": "special_ad_categories", "value": "[]", "type": "query"},
        ],
    )
    payload = {
        "dry_run": False,
        "alterado": True,
        "status": "PAUSED",
        "resultado": result.get("data", result),
    }
    audit_event(
        tool="meta_online",
        action="criar_campanha_meta_pausada",
        target=_normalize_ad_account_id(ad_account_id),
        after=payload,
        status="ok",
    )
    return payload
