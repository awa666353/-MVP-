"""从 CSV / JSON 加载 SeedHospital 列表。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd
from loguru import logger

from hospital_crawler.models import SeedHospital


def load_seeds_csv(path: Path) -> list[SeedHospital]:
    """读取 CSV，列名：name, official_url, province, city, adapter_id, notes（后四列可选）。"""
    if not path.exists():
        logger.error("种子文件不存在: {}", path)
        return []
    df = pd.read_csv(path, dtype=str).fillna("")
    required = {"name", "official_url"}
    cols = set(df.columns.str.strip())
    if not required.issubset(cols):
        raise ValueError(f"CSV 必须包含列: {required}, 当前: {cols}")
    out: list[SeedHospital] = []
    for _, r in df.iterrows():
        try:
            out.append(
                SeedHospital(
                    name=str(r["name"]).strip(),
                    official_url=str(r["official_url"]).strip(),
                    province=str(r.get("province", "") or "").strip(),
                    city=str(r.get("city", "") or "").strip(),
                    adapter_id=str(r.get("adapter_id", "generic") or "generic").strip(),
                    notes=str(r.get("notes", "") or "").strip(),
                )
            )
        except Exception as e:
            logger.warning("跳过无效行: {} err={}", r.to_dict(), e)
    return out


def load_seeds_json(path: Path) -> list[SeedHospital]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "hospitals" in raw:
        raw = raw["hospitals"]
    if not isinstance(raw, list):
        raise ValueError("JSON 应为对象列表或 {hospitals: []}")
    return [SeedHospital.model_validate(x) for x in raw]


def load_seeds(path: Path) -> list[SeedHospital]:
    suf = path.suffix.lower()
    if suf == ".csv":
        return load_seeds_csv(path)
    if suf == ".json":
        return load_seeds_json(path)
    raise ValueError(f"不支持的种子格式: {suf}")


def iter_limited(seeds: Iterable[SeedHospital], limit: int | None) -> list[SeedHospital]:
    items = list(seeds)
    if limit is None or limit <= 0:
        return items
    return items[:limit]
