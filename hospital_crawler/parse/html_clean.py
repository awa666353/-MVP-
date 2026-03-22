"""去除导航、页脚、脚本，提取正文近似文本。"""

from __future__ import annotations

import re
from typing import Iterable

from bs4 import BeautifulSoup, Comment

# 常见噪音标签
NOISE_TAGS: Iterable[str] = (
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
)


def strip_noise(soup: BeautifulSoup) -> None:
    """原地删除噪音节点。"""
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()


def extract_main_text(html: str, max_len: int = 12000) -> str:
    """
    优先 article/main/#content 等区域，否则全 body。
    """
    soup = BeautifulSoup(html, "lxml")
    strip_noise(soup)
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|main|article|intro", re.I))
        or soup.find(class_=re.compile(r"content|article|main|detail|intro", re.I))
        or soup.body
    )
    if not main:
        return ""
    text = main.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    if len(text) > max_len:
        text = text[:max_len] + "\n...[truncated]"
    return text.strip()
