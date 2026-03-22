"""通用兜底：任意页尝试抽电话、地址、一段简介。"""

from __future__ import annotations

from hospital_crawler.models import HospitalExtracted, ParsedPageBundle
from hospital_crawler.parse.base import ParseContext
from hospital_crawler.parse.contact_parser import ContactParser
from hospital_crawler.parse.html_clean import extract_main_text


class GenericFallbackParser:
    name = "generic_fallback"

    def match(self, ctx: ParseContext) -> bool:
        return True  # 最后执行

    def parse(self, ctx: ParseContext) -> ParsedPageBundle:
        text = extract_main_text(ctx.html, max_len=6000)
        cp = ContactParser()
        sub = cp.parse(ctx)
        h = sub.hospital_partial
        if not h.introduction and len(text) > 80:
            h.introduction = text[:4000]
        h.primary_source_url = ctx.final_url or ctx.url
        if not h.phone:
            # ContactParser 已填
            pass
        return ParsedPageBundle(page_type="generic", hospital_partial=h, extra={})
