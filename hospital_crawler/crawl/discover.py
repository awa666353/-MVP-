"""
站内链接发现与优先级排序。
基于锚文本、href、路径关键词打分。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from hospital_crawler.keywords import PAGE_KEYWORDS


@dataclass(order=True)
class DiscoveredLink:
    """分数越高越优先抓取。"""

    score: float
    url: str = field(compare=False)
    anchor_text: str = field(default="", compare=False)
    page_type_hint: str = field(default="unknown", compare=False)


def _same_site(base: str, target: str) -> bool:
    a, b = urlparse(base), urlparse(target)
    return a.netloc.lower() == b.netloc.lower() and b.scheme in ("http", "https", "")


def _score_anchor(anchor: str, href: str) -> tuple[float, str]:
    """返回 (分数, 最匹配的页面类型 hint)。"""
    text = (anchor + " " + href).lower()
    best = 0.0
    best_type = "unknown"
    for ptype, kws in PAGE_KEYWORDS.items():
        s = 0.0
        for kw in kws:
            if kw.lower() in text:
                s += 3.0 + min(len(kw), 8) * 0.1
        if s > best:
            best, best_type = s, ptype
    # 浅层路径略加分
    path_depth = len([x for x in urlparse(href).path.split("/") if x])
    bonus = max(0, 4 - path_depth) * 0.2
    return best + bonus, best_type


def discover_links(
    base_page_url: str,
    html: str,
    max_links: int = 80,
) -> list[DiscoveredLink]:
    """从首页 HTML 提取站内 a 标签，按关键词打分排序。"""
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    out: list[DiscoveredLink] = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full = urljoin(base_page_url, href)
        if not _same_site(base_page_url, full):
            continue
        # 过滤常见非 HTML
        low = full.lower()
        if any(low.endswith(ext) for ext in (".pdf", ".zip", ".jpg", ".png", ".gif", ".doc", ".docx")):
            continue
        if full in seen:
            continue
        seen.add(full)
        anchor = re.sub(r"\s+", " ", a.get_text(" ", strip=True) or "")
        score, hint = _score_anchor(anchor, full)
        if score <= 0:
            score = 0.1  # 低优先级兜底，仍可能有用
        out.append(DiscoveredLink(score=score, url=full, anchor_text=anchor, page_type_hint=hint))
    out.sort(key=lambda x: x.score, reverse=True)
    return out[:max_links]


def filter_by_depth(seed_url: str, urls: Iterable[str], max_depth: int) -> list[str]:
    """按路径深度粗略过滤（与首页同 host，路径段数不超过 max_depth）。"""
    seed_path = urlparse(seed_url).path.rstrip("/") or "/"
    seed_depth = len([x for x in seed_path.split("/") if x])
    kept: list[str] = []
    for u in urls:
        p = urlparse(u)
        depth = len([x for x in p.path.split("/") if x])
        if depth - seed_depth <= max_depth:
            kept.append(u)
    return kept
