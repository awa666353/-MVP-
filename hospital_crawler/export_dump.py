"""从 SQLite 导出 CSV / JSON，便于抽检与对接 RAG。"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from hospital_crawler.config import EXPORT_DIR


def export_sqlite(db_path: Path, out_dir: Path | None = None) -> tuple[Path, Path]:
    out = out_dir or EXPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    conn = sqlite3.connect(db_path)
    try:
        hospitals = pd.read_sql_query("SELECT * FROM hospitals", conn)
        h_csv = out / f"hospitals_{stamp}.csv"
        h_json = out / f"hospitals_{stamp}.json"
        hospitals.to_csv(h_csv, index=False, encoding="utf-8-sig")
        hospitals.to_json(h_json, orient="records", force_ascii=False, indent=2)
        # 子表
        for table in ("hospital_departments", "hospital_registration_methods", "hospital_sources"):
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                df.to_csv(out / f"{table}_{stamp}.csv", index=False, encoding="utf-8-sig")
            except Exception:
                pass
        # 待复核：低置信度
        hospitals["confidence_score"] = pd.to_numeric(hospitals["confidence_score"], errors="coerce")
        review = hospitals[hospitals["confidence_score"] < 0.45]
        review_path = out / f"review_queue_{stamp}.csv"
        review.to_csv(review_path, index=False, encoding="utf-8-sig")
    finally:
        conn.close()
    return h_csv, h_json
