"""联系方式：电话、地址、邮编。"""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

from hospital_crawler.models import HospitalExtracted, ParsedPageBundle, SourceProvenance
from hospital_crawler.parse.base import ParseContext
from hospital_crawler.parse.html_clean import extract_main_text


PHONE_RE = re.compile(
    r"(?:\+?86[-\s]?)?(?:0\d{2,3}[-\s]?\d{7,8}|1[3-9]\d{9}|400[-\s]?\d{3}[-\s]?\d{4})"
)
POSTAL_RE = re.compile(r"\b\d{6}\b")
ADDR_KEYWORDS = ("地址", "院区", "位于", "座落于", "来院")


class ContactParser:
    name = "contact_parser"

    def match(self, ctx: ParseContext) -> bool:
        t = (ctx.title + ctx.page_type_hint).lower()
        return ctx.page_type_hint == "contact" or any(k in t for k in ("联系", "交通", "地址", "来院"))

    def parse(self, ctx: ParseContext) -> ParsedPageBundle:
        soup = BeautifulSoup(ctx.html, "lxml")
        text = extract_main_text(ctx.html, max_len=8000)
        phones = list(dict.fromkeys(PHONE_RE.findall(text)))
        postals = list(dict.fromkeys(POSTAL_RE.findall(text)))
        addr = ""
        for line in text.splitlines():
            if any(k in line for k in ADDR_KEYWORDS) and len(line) > 6:
                addr = line.strip()
                break
        prov = SourceProvenance(
            source_url=ctx.final_url or ctx.url,
            page_title=ctx.title,
            fetched_at=datetime.utcnow(),
            raw_snippet=text[:1200],
        )
        h = HospitalExtracted(
            phone="; ".join(phones[:5]),
            address=addr or "",
            postal_code=postals[0] if postals else "",
            primary_source_url=ctx.final_url or ctx.url,
        )
        if addr or phones:
            h.introduction = ""  # 不在此填充简介
        return ParsedPageBundle(
            page_type="contact",
            hospital_partial=h,
            extra={"phones": phones, "postals": postals},
        )
