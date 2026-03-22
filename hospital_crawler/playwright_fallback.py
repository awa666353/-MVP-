"""
Playwright 兜底：仅当 httpx 无法拿到有效 HTML 时可选调用。
不强制安装：未安装 playwright 时本模块返回 None。

使用前需执行: playwright install chromium
"""

from __future__ import annotations

from typing import Optional


async def fetch_html_playwright(url: str, timeout_ms: int = 30000) -> Optional[str]:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            html = await page.content()
            await browser.close()
            return html
    except Exception:
        return None
