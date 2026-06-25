# -*- coding: utf-8 -*-
"""
SQLite-backed audit log for local and future online MCP operations.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "mcp_local.db"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS companies (
                company_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                meta_ad_account_id TEXT,
                meta_pixel_id TEXT,
                facebook_page_id TEXT,
                instagram_account_id TEXT,
                whatsapp TEXT,
                crm_name TEXT,
                erp_name TEXT,
                google_sheet_id TEXT,
                ga4_property_id TEXT,
                gtm_container_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS company_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id TEXT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
                service TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                external_account_id TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(company_id, service)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                company_id TEXT,
                actor TEXT NOT NULL,
                tool TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                before_json TEXT,
                after_json TEXT,
                status TEXT NOT NULL,
                message TEXT,
                metadata_json TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_audit_company_ts
                ON audit_logs(company_id, ts);
            CREATE INDEX IF NOT EXISTS idx_connections_company
                ON company_connections(company_id);
            """
        )


def to_json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def audit_event(
    *,
    tool: str,
    action: str,
    company_id: str | None = None,
    actor: str = "local-user",
    target: str | None = None,
    before: Any = None,
    after: Any = None,
    status: str = "ok",
    message: str = "",
    metadata: Any = None,
) -> int:
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO audit_logs (
                ts, company_id, actor, tool, action, target, before_json,
                after_json, status, message, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _utc_now(),
                company_id,
                actor,
                tool,
                action,
                target,
                to_json(before),
                to_json(after),
                status,
                message,
                to_json(metadata),
            ),
        )
        return int(cur.lastrowid)


def list_audit_logs(company_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    init_db()
    limit = max(1, min(int(limit), 200))
    with get_connection() as conn:
        if company_id:
            rows = conn.execute(
                """
                SELECT * FROM audit_logs
                WHERE company_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (company_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    result = []
    for row in rows:
        item = dict(row)
        for key in ("before_json", "after_json", "metadata_json"):
            if item.get(key):
                item[key.replace("_json", "")] = json.loads(item[key])
            item.pop(key, None)
        result.append(item)
    return result

