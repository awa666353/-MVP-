"""SQLite 异步封装：建表、简单查询。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from hospital_crawler.config import DEFAULT_DB_PATH


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


async def init_db(db_path: Path | None = None) -> None:
    """执行 schema.sql 创建表与索引。"""
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    async with aiosqlite.connect(path) as db:
        await db.executescript(sql)
        await db.commit()


def sync_init_db(db_path: Path | None = None) -> None:
    """同步建表（CLI / 测试用）。"""
    import sqlite3

    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


async def upsert_hospital_row(
    db_path: Path,
    row: dict[str, Any],
    hospital_id: Optional[int] = None,
) -> int:
    """
    插入或更新医院主表；按 website_url 唯一。
    返回 hospital_id。
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id FROM hospitals WHERE website_url = ?",
            (row["website_url"],),
        )
        existing = await cur.fetchone()
        flags_json = json.dumps(row.get("review_flags") or [], ensure_ascii=False)

        if existing:
            hid = int(existing["id"])
            await db.execute(
                """
                UPDATE hospitals SET
                    name=?, short_name=?, level=?, nature=?, province=?, city=?,
                    address=?, phone=?, postal_code=?, introduction=?,
                    registration_entry_url=?, outpatient_hours=?, visit_notes=?,
                    supports_appointment=?, latitude=?, longitude=?,
                    featured_tech=?, expert_team_url=?, branch_campus_info=?,
                    emergency_info=?, internet_hospital_info=?,
                    confidence_score=?, review_flags=?, adapter_id=?,
                    last_crawled_at=?, updated_at=datetime('now')
                WHERE id=?
                """,
                (
                    row["name"],
                    row.get("short_name", ""),
                    row.get("level", ""),
                    row.get("nature", ""),
                    row.get("province", ""),
                    row.get("city", ""),
                    row.get("address", ""),
                    row.get("phone", ""),
                    row.get("postal_code", ""),
                    row.get("introduction", ""),
                    row.get("registration_entry_url", ""),
                    row.get("outpatient_hours", ""),
                    row.get("visit_notes", ""),
                    row.get("supports_appointment"),
                    row.get("latitude"),
                    row.get("longitude"),
                    row.get("featured_tech", ""),
                    row.get("expert_team_url", ""),
                    row.get("branch_campus_info", ""),
                    row.get("emergency_info", ""),
                    row.get("internet_hospital_info", ""),
                    row.get("confidence_score", 0),
                    flags_json,
                    row.get("adapter_id", "generic"),
                    row.get("last_crawled_at"),
                    hid,
                ),
            )
        else:
            await db.execute(
                """
                INSERT INTO hospitals (
                    name, short_name, level, nature, province, city, address, phone,
                    postal_code, website_url, introduction, registration_entry_url,
                    outpatient_hours, visit_notes, supports_appointment,
                    latitude, longitude, featured_tech, expert_team_url,
                    branch_campus_info, emergency_info, internet_hospital_info,
                    confidence_score, review_flags, adapter_id, last_crawled_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    row["name"],
                    row.get("short_name", ""),
                    row.get("level", ""),
                    row.get("nature", ""),
                    row.get("province", ""),
                    row.get("city", ""),
                    row.get("address", ""),
                    row.get("phone", ""),
                    row.get("postal_code", ""),
                    row["website_url"],
                    row.get("introduction", ""),
                    row.get("registration_entry_url", ""),
                    row.get("outpatient_hours", ""),
                    row.get("visit_notes", ""),
                    row.get("supports_appointment"),
                    row.get("latitude"),
                    row.get("longitude"),
                    row.get("featured_tech", ""),
                    row.get("expert_team_url", ""),
                    row.get("branch_campus_info", ""),
                    row.get("emergency_info", ""),
                    row.get("internet_hospital_info", ""),
                    row.get("confidence_score", 0),
                    flags_json,
                    row.get("adapter_id", "generic"),
                    row.get("last_crawled_at"),
                ),
            )
            cur2 = await db.execute("SELECT last_insert_rowid()")
            rid = await cur2.fetchone()
            hid = int(rid[0])
        await db.commit()
        return hid
