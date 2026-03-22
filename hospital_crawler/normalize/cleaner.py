"""文本清洗、枚举标准化、字段归一。"""

from __future__ import annotations

import re
from typing import Iterable

from hospital_crawler.models import DepartmentItem, HospitalExtracted, RegistrationMethodItem

_WS = re.compile(r"\s+")


def collapse_whitespace(s: str) -> str:
    return _WS.sub(" ", (s or "").strip())


def dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        x = collapse_whitespace(x)
        if not x or x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


REG_LABEL_ZH: dict[str, str] = {
    "wechat": "微信/公众号",
    "wechat_mini": "微信小程序",
    "alipay": "支付宝",
    "web": "官网/网页",
    "phone": "电话",
    "onsite": "现场/窗口",
    "kiosk": "自助机",
    "third_party": "第三方平台",
    "online_booking": "在线预约",
    "general_outpatient": "门诊服务",
}


def normalize_registration_methods(methods: list[RegistrationMethodItem]) -> list[RegistrationMethodItem]:
    by_code: dict[str, RegistrationMethodItem] = {}
    for m in methods:
        code = m.method_code.strip()
        if not code:
            continue
        label = m.method_label_zh or REG_LABEL_ZH.get(code, code)
        if code in by_code:
            continue
        by_code[code] = RegistrationMethodItem(
            method_code=code,
            method_label_zh=label,
            detail_text=collapse_whitespace(m.detail_text),
            booking_url=m.booking_url.strip(),
            supports_booking=m.supports_booking,
            provenance=m.provenance,
        )
    return list(by_code.values())


def normalize_departments(depts: list[DepartmentItem]) -> list[DepartmentItem]:
    seen: set[tuple[str, str]] = set()
    out: list[DepartmentItem] = []
    for d in depts:
        name = collapse_whitespace(d.name)
        if len(name) < 2:
            continue
        key = (name[:120], d.category)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            DepartmentItem(
                name=name[:200],
                category=d.category or "general",
                description=collapse_whitespace(d.description),
                provenance=d.provenance,
            )
        )
    return out


def merge_hospital_fields(base: HospitalExtracted, incoming: HospitalExtracted) -> HospitalExtracted:
    """
    非空覆盖策略：incoming 有值则覆盖 base 空字段；
    列表类字段合并。
    """
    data = base.model_dump()
    inc = incoming.model_dump()
    for k, v in inc.items():
        if k in ("registration_methods", "departments", "review_flags"):
            continue
        if k == "introduction" and isinstance(v, str) and v.strip():
            cur = (data.get("introduction") or "").strip()
            if len(v) > len(cur):
                data["introduction"] = v
            continue
        if v not in (None, "", [], {}):
            if data.get(k) in (None, "", []):
                data[k] = v
    data["registration_methods"] = normalize_registration_methods(
        base.registration_methods + incoming.registration_methods
    )
    data["departments"] = normalize_departments(base.departments + incoming.departments)
    return HospitalExtracted.model_validate(data)
