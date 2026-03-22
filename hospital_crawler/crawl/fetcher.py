"""异步 HTTP 抓取：超时、重试、限流。"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from typing import Optional

import httpx
from loguru import logger

from hospital_crawler.config import DEFAULT_USER_AGENT, MAX_CONCURRENT_REQUESTS, REQUEST_TIMEOUT_SEC


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    headers: dict
    text: str
    content: bytes
    error: Optional[str] = None

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


class AsyncFetcher:
    """带连接池限制的 httpx AsyncClient；失败自动重试（tenacity 风格退避）。"""

    def __init__(self) -> None:
        limits = httpx.Limits(max_connections=MAX_CONCURRENT_REQUESTS, max_keepalive_connections=5)
        self._client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_SEC,
            follow_redirects=True,
            limits=limits,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def fetch(self, url: str) -> FetchResult:
        last_err: Optional[BaseException] = None
        for i in range(3):
            try:
                r = await self._client.get(url)
                return FetchResult(
                    url=url,
                    final_url=str(r.url),
                    status_code=r.status_code,
                    headers=dict(r.headers),
                    text=r.text,
                    content=r.content,
                )
            except (httpx.TimeoutException, httpx.TransportError) as e:
                last_err = e
                wait = min(10.0, 0.5 * (2**i))
                logger.debug("fetch 重试 {} 第{}次: {}", url, i + 1, e)
                await asyncio.sleep(wait)
        assert last_err is not None
        raise last_err
