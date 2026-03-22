"""
简单置信度评分：标题匹配、文本长度、关键词命中、多源交叉（占位）。
返回 0~1 及 review_flags。
"""

from __future__ import annotations

from hospital_crawler.keywords import DEPARTMENT_HIGHLIGHT_KEYWORDS, PAGE_KEYWORDS
from hospital_crawler.models import HospitalExtracted


def _flatten_keywords() -> set[str]:
    s: set[str] = set()
    for kws in PAGE_KEYWORDS.values():
        for k in kws:
            s.add(k)
    return s


ALL_NAV_KWS = _flatten_keywords()


def score_hospital(h: HospitalExtracted, source_titles: list[str]) -> tuple[float, list[str]]:
    """
    source_titles: 本次抓取涉及页面的标题列表，用于弱交叉验证。
    """
    flags: list[str] = []
    score = 0.35

    if len(h.introduction or "") > 200:
        score += 0.15
    elif len(h.introduction or "") < 40:
        flags.append("introduction_too_short")
        score -= 0.1

    if h.phone and len(h.phone) >= 8:
        score += 0.1
    if h.address and len(h.address) > 5:
        score += 0.1
    if h.registration_methods:
        score += 0.1
    if h.departments:
        score += 0.08

    intro = h.introduction or ""
    hit = sum(1 for kw in DEPARTMENT_HIGHLIGHT_KEYWORDS if kw in intro)
    if hit:
        score += min(0.1, 0.02 * hit)

    # 标题是否与栏目词相关
    title_blob = " ".join(source_titles)
    nav_hit = sum(1 for k in ALL_NAV_KWS if k in title_blob)
    if nav_hit >= 2:
        score += 0.05

    if len(source_titles) >= 3:
        score += 0.05

    if not h.name and not h.introduction:
        flags.append("missing_core_identity")
        score -= 0.2

    score = max(0.0, min(1.0, score))
    return score, flags
