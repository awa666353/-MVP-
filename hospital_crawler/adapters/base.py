"""适配器基类：在通用解析前后钩子。"""

from __future__ import annotations

from typing import Optional

from hospital_crawler.models import HospitalExtracted, ParsedPageBundle, SeedHospital
from hospital_crawler.parse.base import ParseContext


class HospitalSiteAdapter:
    """
    adapter_id 与种子 CSV 中 adapter_id 对应。
    子类可覆盖 discover_filter、post_parse_merge。
    """

    adapter_id: str = "generic"

    def adjust_seed_url(self, seed: SeedHospital) -> SeedHospital:
        return seed

    def discover_filter(self, url: str, anchor_text: str) -> bool:
        """返回 False 则丢弃该链接。"""
        return True

    def parse_override(
        self, ctx: ParseContext
    ) -> Optional[ParsedPageBundle]:
        """若返回非 None，则跳过通用解析链直接使用该结果。"""
        return None

    def post_parse_merge(
        self, seed: SeedHospital, merged: HospitalExtracted
    ) -> HospitalExtracted:
        """全页合并后的最后修正（如固定医院名）。"""
        if not merged.name.strip():
            merged.name = seed.name
        if not merged.province:
            merged.province = seed.province
        if not merged.city:
            merged.city = seed.city
        if not merged.website_url:
            merged.website_url = seed.official_url
        return merged
