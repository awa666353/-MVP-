"""医院简介 / 概况页解析。"""

from __future__ import annotations

import re
from datetime import datetime

from hospital_crawler.keywords import HOSPITAL_LEVEL_PATTERNS, NATURE_KEYWORDS
from hospital_crawler.models import HospitalExtracted, ParsedPageBundle, SourceProvenance
from hospital_crawler.parse.base import ParseContext
from hospital_crawler.parse.html_clean import extract_main_text


class HospitalProfileParser:
    name = "hospital_profile_parser"

    def match(self, ctx: ParseContext) -> bool:
        return ctx.page_type_hint == "hospital_profile" or any(
            k in ctx.title for k in ("简介", "概况", "介绍", "关于")
        )

    def parse(self, ctx: ParseContext) -> ParsedPageBundle:
        text = extract_main_text(ctx.html, max_len=15000)
        prov = SourceProvenance(
            source_url=ctx.final_url or ctx.url,
            page_title=ctx.title,
            fetched_at=datetime.utcnow(),
            raw_snippet=text[:2000],
        )
        level = ""
        for p in HOSPITAL_LEVEL_PATTERNS:
            if p in text:
                level = p
                break
        nature = ""
        for zh, code in NATURE_KEYWORDS.items():
            if zh in text:
                nature = code
                break
        h = HospitalExtracted(
            introduction=text,
            level=level,
            nature=nature,
            primary_source_url=ctx.final_url or ctx.url,
        )
        # 尝试从正文第一行取“医院名称”弱信号
        first = text.splitlines()[0] if text else ""
        if len(first) < 60 and ("医院" in first or "中心" in first):
            h.name = re.sub(r"\s+", "", first)
        return ParsedPageBundle(
            page_type="hospital_profile",
            hospital_partial=h,
            extra={"provenance_profile": prov.model_dump()},
        )
