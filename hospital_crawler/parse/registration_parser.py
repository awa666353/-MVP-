"""挂号 / 门诊信息解析。"""

from __future__ import annotations

import re
from datetime import datetime

from hospital_crawler.keywords import REGISTRATION_KEYWORD_MAP
from hospital_crawler.models import (
    HospitalExtracted,
    ParsedPageBundle,
    RegistrationMethodItem,
    SourceProvenance,
)
from hospital_crawler.parse.base import ParseContext
from hospital_crawler.parse.html_clean import extract_main_text


class RegistrationParser:
    name = "registration_parser"

    def match(self, ctx: ParseContext) -> bool:
        return ctx.page_type_hint == "registration" or any(
            k in ctx.title for k in ("挂号", "预约", "门诊", "就医", "就诊")
        )

    def parse(self, ctx: ParseContext) -> ParsedPageBundle:
        text = extract_main_text(ctx.html, max_len=10000)
        prov = SourceProvenance(
            source_url=ctx.final_url or ctx.url,
            page_title=ctx.title,
            fetched_at=datetime.utcnow(),
            raw_snippet=text[:1500],
        )
        methods: list[RegistrationMethodItem] = []
        seen: set[str] = set()
        for zh, code in REGISTRATION_KEYWORD_MAP.items():
            if zh in text and code not in seen:
                seen.add(code)
                methods.append(
                    RegistrationMethodItem(
                        method_code=code,
                        method_label_zh=zh,
                        detail_text="",
                        supports_booking=True if "预约" in text or "挂号" in text else None,
                        provenance=prov,
                    )
                )
        supports = None
        if "预约" in text or "网上" in text or "微信" in text:
            supports = True
        # 门诊时间：含“门诊时间”的段落
        hours = ""
        for line in text.splitlines():
            if "门诊时间" in line or "开诊" in line:
                hours = line.strip()
                break
        notes = ""
        if "须知" in text:
            m = re.search(r"(.{0,20}须知.{0,500})", text, re.S)
            if m:
                notes = m.group(1).strip()[:800]
        h = HospitalExtracted(
            registration_entry_url=ctx.final_url or ctx.url,
            outpatient_hours=hours,
            visit_notes=notes,
            supports_appointment=supports,
            registration_methods=methods,
            primary_source_url=ctx.final_url or ctx.url,
        )
        return ParsedPageBundle(page_type="registration", hospital_partial=h, extra={})
