"""robots.txt 解析与路径允许判断（简化版）。"""

from __future__ import annotations

import urllib.robotparser
from functools import lru_cache
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from hospital_crawler.config import DEFAULT_USER_AGENT, REQUEST_TIMEOUT_SEC


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=1, max=8))
def _fetch_robots_txt(robots_url: str) -> Optional[str]:
    with httpx.Client(timeout=REQUEST_TIMEOUT_SEC, follow_redirects=True) as client:
        r = client.get(robots_url, headers={"User-Agent": DEFAULT_USER_AGENT})
        if r.status_code == 404:
            return None
        if r.status_code >= 400:
            # 无权限或网关错误时视为「无 robots 声明」，避免整站不可用；生产可改为保守禁止
            return None
        return r.text


@lru_cache(maxsize=256)
def get_robot_parser(base_url: str) -> urllib.robotparser.RobotFileParser:
    """
    对同一站点根 URL 缓存 RobotFileParser。
    base_url 应为 scheme://host 形式。
    """
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = urljoin(root + "/", "robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        content = _fetch_robots_txt(robots_url)
        if content is None:
            rp.parse([])
        else:
            rp.parse(content.splitlines())
    except Exception as e:
        logger.warning("读取 robots.txt 失败，默认允许: {} err={}", robots_url, e)
        rp.parse([])
    return rp


def can_fetch(url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    rp = get_robot_parser(base)
    return rp.can_fetch(user_agent, url)
