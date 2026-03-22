"""解析器基类与上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hospital_crawler.models import ParsedPageBundle


@dataclass
class ParseContext:
    url: str
    final_url: str
    title: str
    html: str
    page_type_hint: str = "unknown"


class PageParser(Protocol):
    """页面解析器协议。"""

    name: str

    def match(self, ctx: ParseContext) -> bool: ...

    def parse(self, ctx: ParseContext) -> ParsedPageBundle: ...
