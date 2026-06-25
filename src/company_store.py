# -*- coding: utf-8 -*-
"""
Multi-company registry for the local MCP.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from src.audit_log import audit_event, get_connection, init_db


COMPANY_FIELDS = {
    "name",
    "status",
    "meta_ad_account_id",
    "meta_pixel_id",
    "facebook_page_id",
    "instagram_account_id",
    "whatsapp",
    "crm_name",
    "erp_name",
    "google_sheet_id",
    "ga4_property_id",
    "gtm_container_id",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_company_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())
    slug = slug.strip("-")
    return slug or "empresa"


def _normalize_company_id(company_id: str) -> str:
    return slugify_company_id(company_id)


def upsert_company(data: dict[str, Any], actor: str = "local-user") -> dict[str, Any]:
    init_db()
    if not data.get("name") and not data.get("company_id"):
        raise ValueError("Informe name ou company_id.")

    company_id = _normalize_company_id(data.get("company_id") or data["name"])
    now = _utc_now()
    clean = {key: data.get(key) for key in COMPANY_FIELDS if key in data}
    clean.setdefault("name", data.get("name") or company_id)
    clean.setdefault("status", "active")

    with get_connection() as conn:
        before_row = conn.execute(
            "SELECT * FROM companies WHERE company_id = ?",
            (company_id,),
        ).fetchone()
        before = dict(before_row) if before_row else None

        row = {
            "company_id": company_id,
            "name": clean.get("name"),
            "status": clean.get("status"),
            "meta_ad_account_id": clean.get("meta_ad_account_id"),
            "meta_pixel_id": clean.get("meta_pixel_id"),
            "facebook_page_id": clean.get("facebook_page_id"),
            "instagram_account_id": clean.get("instagram_account_id"),
            "whatsapp": clean.get("whatsapp"),
            "crm_name": clean.get("crm_name"),
            "erp_name": clean.get("erp_name"),
            "google_sheet_id": clean.get("google_sheet_id"),
            "ga4_property_id": clean.get("ga4_property_id"),
            "gtm_container_id": clean.get("gtm_container_id"),
            "created_at": before["created_at"] if before else now,
            "updated_at": now,
        }

        if before:
            for key, value in row.items():
                if value is None and key not in {"updated_at"}:
                    row[key] = before[key]

        conn.execute(
            """
            INSERT INTO companies (
                company_id, name, status, meta_ad_account_id, meta_pixel_id,
                facebook_page_id, instagram_account_id, whatsapp, crm_name,
                erp_name, google_sheet_id, ga4_property_id, gtm_container_id,
                created_at, updated_at
            )
            VALUES (
                :company_id, :name, :status, :meta_ad_account_id, :meta_pixel_id,
                :facebook_page_id, :instagram_account_id, :whatsapp, :crm_name,
                :erp_name, :google_sheet_id, :ga4_property_id, :gtm_container_id,
                :created_at, :updated_at
            )
            ON CONFLICT(company_id) DO UPDATE SET
                name = excluded.name,
                status = excluded.status,
                meta_ad_account_id = excluded.meta_ad_account_id,
                meta_pixel_id = excluded.meta_pixel_id,
                facebook_page_id = excluded.facebook_page_id,
                instagram_account_id = excluded.instagram_account_id,
                whatsapp = excluded.whatsapp,
                crm_name = excluded.crm_name,
                erp_name = excluded.erp_name,
                google_sheet_id = excluded.google_sheet_id,
                ga4_property_id = excluded.ga4_property_id,
                gtm_container_id = excluded.gtm_container_id,
                updated_at = excluded.updated_at
            """,
            row,
        )

    after = get_company(company_id)
    audit_event(
        tool="company_store",
        action="upsert_company",
        company_id=company_id,
        actor=actor,
        target=company_id,
        before=before,
        after=after,
        status="ok",
    )
    return after


def get_company(company_id: str) -> dict[str, Any]:
    init_db()
    normalized = _normalize_company_id(company_id)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM companies WHERE company_id = ?",
            (normalized,),
        ).fetchone()
    if not row:
        raise ValueError(f"Empresa nao encontrada: {normalized}")
    return dict(row)


def list_companies(include_inactive: bool = False) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        if include_inactive:
            rows = conn.execute("SELECT * FROM companies ORDER BY name").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM companies WHERE status = 'active' ORDER BY name"
            ).fetchall()
    return [dict(row) for row in rows]


def upsert_company_connection(
    company_id: str,
    service: str,
    status: str = "pending",
    external_account_id: str = "",
    notes: str = "",
    actor: str = "local-user",
) -> dict[str, Any]:
    init_db()
    company = get_company(company_id)
    now = _utc_now()
    service = service.strip().lower()
    with get_connection() as conn:
        before_row = conn.execute(
            "SELECT * FROM company_connections WHERE company_id = ? AND service = ?",
            (company["company_id"], service),
        ).fetchone()
        before = dict(before_row) if before_row else None
        conn.execute(
            """
            INSERT INTO company_connections (
                company_id, service, status, external_account_id, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_id, service) DO UPDATE SET
                status = excluded.status,
                external_account_id = excluded.external_account_id,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            (
                company["company_id"],
                service,
                status,
                external_account_id,
                notes,
                before["created_at"] if before else now,
                now,
            ),
        )
        after_row = conn.execute(
            "SELECT * FROM company_connections WHERE company_id = ? AND service = ?",
            (company["company_id"], service),
        ).fetchone()

    after = dict(after_row)
    audit_event(
        tool="company_store",
        action="upsert_company_connection",
        company_id=company["company_id"],
        actor=actor,
        target=service,
        before=before,
        after=after,
        status="ok",
    )
    return after


def list_company_connections(company_id: str) -> list[dict[str, Any]]:
    init_db()
    company = get_company(company_id)
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM company_connections
            WHERE company_id = ?
            ORDER BY service
            """,
            (company["company_id"],),
        ).fetchall()
    return [dict(row) for row in rows]

