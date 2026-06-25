# -*- coding: utf-8 -*-
"""
Local encrypted-at-rest substitute for a future cloud vault.

This stores only per-company references in the MCP database and keeps secret
values in ignored JSON files. It is not a shared cloud vault; it is the safe
local boundary before moving to Supabase/Render/AWS secrets.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.audit_log import audit_event
from src.company_store import get_company

BASE_DIR = Path(__file__).resolve().parent.parent
SECRETS_DIR = BASE_DIR / "secrets" / "companies"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_path(company_id: str) -> Path:
    company = get_company(company_id)
    return SECRETS_DIR / f"{company['company_id']}.json"


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def load_secret_metadata(company_id: str) -> dict[str, Any]:
    path = _secret_path(company_id)
    if not path.exists():
        return {"company_id": get_company(company_id)["company_id"], "secrets": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    secrets = data.get("secrets", {})
    return {
        "company_id": data.get("company_id"),
        "updated_at": data.get("updated_at"),
        "secrets": {
            key: {
                "present": bool(item.get("value")),
                "masked": _mask(str(item.get("value", ""))),
                "fingerprint": _fingerprint(str(item.get("value", ""))) if item.get("value") else "",
                "updated_at": item.get("updated_at"),
            }
            for key, item in secrets.items()
        },
    }


def save_company_secret(
    company_id: str,
    service: str,
    key: str,
    value: str,
    actor: str = "local-user",
) -> dict[str, Any]:
    company = get_company(company_id)
    service = service.strip().lower()
    key = key.strip().upper()
    if not service or not key or not value:
        raise ValueError("Informe company_id, service, key e value.")

    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    path = _secret_path(company["company_id"])
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"company_id": company["company_id"], "secrets": {}}

    secret_key = f"{service}.{key}"
    before_meta = load_secret_metadata(company["company_id"]).get("secrets", {}).get(secret_key)
    data.setdefault("secrets", {})[secret_key] = {
        "service": service,
        "key": key,
        "value": value,
        "updated_at": _utc_now(),
    }
    data["updated_at"] = _utc_now()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    after_meta = load_secret_metadata(company["company_id"])["secrets"][secret_key]
    audit_event(
        tool="secret_vault",
        action="save_company_secret",
        company_id=company["company_id"],
        actor=actor,
        target=secret_key,
        before=before_meta,
        after=after_meta,
        status="ok",
        message="Valor secreto salvo em arquivo local ignorado pelo git.",
    )
    return {
        "company_id": company["company_id"],
        "service": service,
        "key": key,
        "secret_ref": secret_key,
        "masked": after_meta["masked"],
        "fingerprint": after_meta["fingerprint"],
        "stored_locally": True,
        "path_exposta": False,
    }

