"""
端到端流水线：种子 -> 首页 -> 发现链接 -> 分层抓取 -> 多解析器 -> 合并 -> 评分 -> 入库。
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from loguru import logger

from hospital_crawler.adapters.registry import get_adapter
from hospital_crawler.config import (
    LOW_CONFIDENCE_THRESHOLD,
    MAX_CRAWL_DEPTH,
    MAX_PAGES_PER_HOSPITAL,
    MIN_REQUEST_INTERVAL_SEC,
    RESPECT_ROBOTS_TXT,
)
from hospital_crawler.crawl.discover import discover_links, filter_by_depth
from hospital_crawler.crawl.fetcher import AsyncFetcher, FetchResult
from hospital_crawler.crawl.robots import can_fetch
from hospital_crawler.models import HospitalExtracted, ParsedPageBundle, RawPageRecord, SeedHospital
from hospital_crawler.normalize.cleaner import merge_hospital_fields
from hospital_crawler.parse.base import ParseContext
from hospital_crawler.parse.contact_parser import ContactParser
from hospital_crawler.parse.department_parser import DepartmentParser
from hospital_crawler.parse.generic import GenericFallbackParser
from hospital_crawler.parse.profile_parser import HospitalProfileParser
from hospital_crawler.parse.registration_parser import RegistrationParser
from hospital_crawler.review.scorer import score_hospital
from hospital_crawler.storage.repository import cache_url_fetched, log_crawl_sync, persist_hospital, was_url_unchanged


def _title_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    t = soup.title
    return (t.string or "").strip() if t else ""


def _record_from_fetch(url: str, fr: FetchResult) -> RawPageRecord:
    return RawPageRecord(
        url=url,
        final_url=fr.final_url,
        http_status=fr.status_code,
        content_type=fr.headers.get("content-type", ""),
        title=_title_from_html(fr.text),
        html_sha256=fr.content_sha256,
        text_preview=(fr.text or "")[:8000],
    )


class CrawlPipeline:
    """单医院抓取流水线（async）。"""

    def __init__(self, db_path, respect_robots: bool = RESPECT_ROBOTS_TXT) -> None:
        from pathlib import Path

        self.db_path = Path(db_path)
        self.respect_robots = respect_robots
        self._fetcher: Optional[AsyncFetcher] = None
        self._parsers = [
            HospitalProfileParser(),
            RegistrationParser(),
            DepartmentParser(),
            ContactParser(),
        ]
        self._generic = GenericFallbackParser()

    async def __aenter__(self) -> "CrawlPipeline":
        self._fetcher = AsyncFetcher()
        return self

    async def __aexit__(self, *args) -> None:
        if self._fetcher:
            await self._fetcher.aclose()

    def _parse_chain(self, ctx: ParseContext) -> ParsedPageBundle:
        """按顺序匹配专用解析器；若无匹配则通用兜底。"""
        merged = HospitalExtracted()
        any_match = False
        for p in self._parsers:
            if p.match(ctx):
                any_match = True
                b = p.parse(ctx)
                merged = merge_hospital_fields(merged, b.hospital_partial)
        if not any_match:
            b = self._generic.parse(ctx)
            merged = merge_hospital_fields(merged, b.hospital_partial)
        return ParsedPageBundle(page_type=ctx.page_type_hint, hospital_partial=merged)

    async def _allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        return await asyncio.to_thread(can_fetch, url)

    async def _fetch_page(
        self, url: str, seed_name: str, *, allow_skip_parse_on_unchanged: bool = True
    ) -> Optional[tuple[RawPageRecord, str]]:
        """
        单次 HTTP GET，返回 (存档记录, HTML 全文)。
        子页若内容哈希未变可跳过解析（省 CPU）；首页始终返回 HTML 以便链接发现。
        """
        assert self._fetcher is not None
        await asyncio.sleep(MIN_REQUEST_INTERVAL_SEC)
        if not await self._allowed(url):
            log_crawl_sync(self.db_path, url, "skipped_robots", "robots disallow", seed_name)
            logger.info("robots 禁止: {}", url)
            return None
        try:
            fr = await self._fetcher.fetch(url)
        except Exception as e:
            log_crawl_sync(self.db_path, url, "error", str(e), seed_name)
            logger.warning("抓取失败 {}: {}", url, e)
            return None
        rp = _record_from_fetch(url, fr)
        if fr.status_code >= 400:
            log_crawl_sync(self.db_path, url, "error", f"HTTP {fr.status_code}", seed_name)
            return rp, ""
        skip_parse = False
        if allow_skip_parse_on_unchanged and was_url_unchanged(
            self.db_path, fr.final_url, fr.content_sha256
        ):
            logger.debug("内容未变，跳过解析: {}", fr.final_url)
            skip_parse = True
        cache_url_fetched(self.db_path, fr.final_url, fr.content_sha256)
        log_crawl_sync(self.db_path, url, "success", "unchanged_skip_parse" if skip_parse else "", seed_name)
        html = fr.text or ""
        if skip_parse:
            html = ""
        return rp, html

    async def run_seed(self, seed: SeedHospital) -> HospitalExtracted:
        adapter = get_adapter(seed.adapter_id)
        seed = adapter.adjust_seed_url(seed)
        home = seed.official_url.strip()
        if not home.startswith(("http://", "https://")):
            home = "https://" + home

        raw_records: list[RawPageRecord] = []
        source_titles: list[str] = []

        first = await self._fetch_page(home, seed.name, allow_skip_parse_on_unchanged=False)
        if not first:
            h = HospitalExtracted(
                name=seed.name,
                website_url=home,
                review_flags=["home_fetch_failed"],
            )
            return adapter.post_parse_merge(seed, h)

        home_rp, home_html = first
        raw_records.append(home_rp)
        merged = HospitalExtracted(name=seed.name, website_url=home)

        if home_html:
            ctx = ParseContext(
                url=home,
                final_url=home_rp.final_url,
                title=_title_from_html(home_html),
                html=home_html,
                page_type_hint="hospital_profile",
            )
            override = adapter.parse_override(ctx)
            part = (
                override.hospital_partial
                if override
                else self._parse_chain(ctx).hospital_partial
            )
            merged = merge_hospital_fields(merged, part)
            source_titles.append(ctx.title)

            discovered = discover_links(home_rp.final_url, home_html, max_links=100)
            candidate_urls = [d.url for d in discovered if adapter.discover_filter(d.url, d.anchor_text)]
            candidate_urls = filter_by_depth(home, candidate_urls, MAX_CRAWL_DEPTH)
            home_norm = home_rp.final_url.rstrip("/")
            candidate_urls = [u for u in candidate_urls if u.rstrip("/") != home_norm][
                : MAX_PAGES_PER_HOSPITAL - 1
            ]

            seen: set[str] = set()
            ordered_links = []
            for d in discovered:
                if d.url in candidate_urls and d.url not in seen:
                    seen.add(d.url)
                    ordered_links.append(d)

            for d in ordered_links:
                got = await self._fetch_page(d.url, seed.name, allow_skip_parse_on_unchanged=True)
                if not got:
                    continue
                sub_rp, body = got
                raw_records.append(sub_rp)
                if not body or sub_rp.http_status >= 400:
                    continue
                ctx2 = ParseContext(
                    url=d.url,
                    final_url=sub_rp.final_url,
                    title=_title_from_html(body),
                    html=body,
                    page_type_hint=d.page_type_hint,
                )
                ov = adapter.parse_override(ctx2)
                part2 = (
                    ov.hospital_partial
                    if ov
                    else self._parse_chain(ctx2).hospital_partial
                )
                merged = merge_hospital_fields(merged, part2)
                source_titles.append(ctx2.title)

        merged.last_crawled_at = datetime.utcnow()
        merged = adapter.post_parse_merge(seed, merged)
        conf, flags = score_hospital(merged, source_titles)
        merged.confidence_score = conf
        merged.review_flags = list(dict.fromkeys(merged.review_flags + flags))
        if conf < LOW_CONFIDENCE_THRESHOLD:
            merged.review_flags.append("low_confidence")

        await persist_hospital(self.db_path, seed, merged, raw_records)
        logger.info(
            "完成 {} 置信度={:.2f} 标记={}",
            seed.name,
            merged.confidence_score,
            merged.review_flags,
        )
        return merged
