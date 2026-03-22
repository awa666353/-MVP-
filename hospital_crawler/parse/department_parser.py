"""重点专科 / 科室列表解析。"""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

from hospital_crawler.keywords import DEPARTMENT_HIGHLIGHT_KEYWORDS
from hospital_crawler.models import DepartmentItem, HospitalExtracted, ParsedPageBundle, SourceProvenance
from hospital_crawler.parse.base import ParseContext
from hospital_crawler.parse.html_clean import extract_main_text, strip_noise


class DepartmentParser:
    name = "department_parser"

    def match(self, ctx: ParseContext) -> bool:
        return ctx.page_type_hint == "department" or any(
            k in ctx.title for k in ("科室", "专科", "学科")
        )

    def parse(self, ctx: ParseContext) -> ParsedPageBundle:
        soup = BeautifulSoup(ctx.html, "lxml")
        strip_noise(soup)
        prov = SourceProvenance(
            source_url=ctx.final_url or ctx.url,
            page_title=ctx.title,
            fetched_at=datetime.utcnow(),
        )
        items: list[DepartmentItem] = []
        # 列表项
        for ul in soup.find_all(["ul", "ol"]):
            for li in ul.find_all("li", recursive=False):
                name = li.get_text(" ", strip=True)
                if not name or len(name) > 100:
                    continue
                cat = "department_list"
                low = name
                for kw in DEPARTMENT_HIGHLIGHT_KEYWORDS:
                    if kw in low:
                        if "国家" in kw:
                            cat = "national_clinical"
                        elif "省" in kw:
                            cat = "provincial"
                        else:
                            cat = "advantage"
                        break
                items.append(DepartmentItem(name=name[:200], category=cat, provenance=prov))

        text = extract_main_text(ctx.html, max_len=10000)
        prov.raw_snippet = text[:1200]
        # 关键词段落拆分
        for kw in DEPARTMENT_HIGHLIGHT_KEYWORDS:
            if kw not in text:
                continue
            idx = text.find(kw)
            chunk = text[idx : idx + 1200]
            for part in re.split(r"[；;\n]", chunk):
                part = part.strip()
                if 2 < len(part) < 60 and not part.startswith(kw):
                    cat = "provincial" if "省" in kw else "national_clinical" if "国家" in kw else "advantage"
                    items.append(DepartmentItem(name=part, category=cat, provenance=prov))

        # 去重按 name
        seen: set[str] = set()
        uniq: list[DepartmentItem] = []
        for d in items:
            key = d.name[:80]
            if key in seen:
                continue
            seen.add(key)
            uniq.append(d)

        h = HospitalExtracted(departments=uniq, primary_source_url=ctx.final_url or ctx.url)
        return ParsedPageBundle(page_type="department", hospital_partial=h, extra={})
