"""将 HospitalExtracted 写入 SQLite，并维护子表与 raw_pages。"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from hospital_crawler.db.database import upsert_hospital_row
from hospital_crawler.models import HospitalExtracted, RawPageRecord, SeedHospital


def _sync_conn(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


async def persist_hospital(
    db_path: Path,
    seed: SeedHospital,
    merged: HospitalExtracted,
    raw_pages: list[RawPageRecord],
) -> int:
    """异步主表 upsert + 同步子表（aiosqlite 与 sqlite3 混用简化 MVP）。"""
    row = {
        "name": merged.name or seed.name,
        "short_name": merged.short_name,
        "level": merged.level,
        "nature": merged.nature,
        "province": merged.province or seed.province,
        "city": merged.city or seed.city,
        "address": merged.address,
        "phone": merged.phone,
        "postal_code": merged.postal_code,
        "website_url": seed.official_url,
        "introduction": merged.introduction,
        "registration_entry_url": merged.registration_entry_url,
        "outpatient_hours": merged.outpatient_hours,
        "visit_notes": merged.visit_notes,
        "supports_appointment": (
            int(merged.supports_appointment)
            if merged.supports_appointment is not None
            else None
        ),
        "latitude": merged.latitude,
        "longitude": merged.longitude,
        "featured_tech": merged.featured_tech,
        "expert_team_url": merged.expert_team_url,
        "branch_campus_info": merged.branch_campus_info,
        "emergency_info": merged.emergency_info,
        "internet_hospital_info": merged.internet_hospital_info,
        "confidence_score": merged.confidence_score,
        "review_flags": merged.review_flags,
        "adapter_id": seed.adapter_id,
        "last_crawled_at": (merged.last_crawled_at or datetime.utcnow()).isoformat() + "Z",
    }
    hid = await upsert_hospital_row(db_path, row)

    conn = _sync_conn(db_path)
    try:
        conn.execute("DELETE FROM hospital_departments WHERE hospital_id=?", (hid,))
        conn.execute("DELETE FROM hospital_registration_methods WHERE hospital_id=?", (hid,))
        conn.execute("DELETE FROM hospital_sources WHERE hospital_id=?", (hid,))

        for d in merged.departments:
            conn.execute(
                """
                INSERT INTO hospital_departments
                (hospital_id, name, category, description, source_url, raw_snippet)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    hid,
                    d.name,
                    d.category,
                    d.description,
                    (d.provenance.source_url if d.provenance else "") or "",
                    (d.provenance.raw_snippet if d.provenance else "") or "",
                ),
            )
        for r in merged.registration_methods:
            conn.execute(
                """
                INSERT INTO hospital_registration_methods
                (hospital_id, method_code, method_label_zh, detail_text, booking_url,
                 supports_booking, source_url, raw_snippet)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    hid,
                    r.method_code,
                    r.method_label_zh,
                    r.detail_text,
                    r.booking_url,
                    int(r.supports_booking) if r.supports_booking is not None else None,
                    (r.provenance.source_url if r.provenance else "") or "",
                    (r.provenance.raw_snippet if r.provenance else "") or "",
                ),
            )
        # 来源：简介、挂号页等（简化：各记一条主 URL）
        if merged.primary_source_url:
            conn.execute(
                """
                INSERT INTO hospital_sources
                (hospital_id, field_name, source_url, page_title, fetched_at, raw_snippet, confidence)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    hid,
                    "aggregate",
                    merged.primary_source_url,
                    "",
                    datetime.utcnow().isoformat() + "Z",
                    (merged.introduction or "")[:2000],
                    merged.confidence_score,
                ),
            )

        for rp in raw_pages:
            conn.execute(
                """
                INSERT INTO raw_pages
                (hospital_id, url, final_url, http_status, content_type, title,
                 html_sha256, text_preview, fetched_at)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    hid,
                    rp.url,
                    rp.final_url,
                    rp.http_status,
                    rp.content_type,
                    rp.title,
                    rp.html_sha256,
                    rp.text_preview,
                    rp.fetched_at.isoformat() + "Z",
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return hid


def log_crawl_sync(
    db_path: Path,
    target_url: str,
    status: str,
    message: str = "",
    seed_name: str = "",
) -> int:
    conn = _sync_conn(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO crawl_logs (hospital_seed_name, target_url, status, message, started_at)
            VALUES (?,?,?,?,?)
            """,
            (seed_name, target_url, status, message, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def cache_url_fetched(db_path: Path, url: str, sha: str) -> None:
    conn = _sync_conn(db_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO fetched_url_cache (url, html_sha256, fetched_at)
            VALUES (?,?,?)
            """,
            (url, sha, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
    finally:
        conn.close()


def was_url_unchanged(db_path: Path, url: str, sha: str) -> bool:
    conn = _sync_conn(db_path)
    try:
        cur = conn.execute(
            "SELECT html_sha256 FROM fetched_url_cache WHERE url=?",
            (url,),
        )
        row = cur.fetchone()
        if not row:
            return False
        return row["html_sha256"] == sha
    finally:
        conn.close()
