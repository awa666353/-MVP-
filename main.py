#!/usr/bin/env python3
"""
CLI：python main.py --input data/seeds.csv --limit 10

也可：python -m hospital_crawler.main （若包内入口）
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

# 保证可从项目根目录运行
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hospital_crawler.config import DATA_DIR, DEFAULT_DB_PATH, EXPORT_DIR
from hospital_crawler.db.database import sync_init_db
from hospital_crawler.export_dump import export_sqlite
from hospital_crawler.pipeline import CrawlPipeline
from hospital_crawler.seed.loader import iter_limited, load_seeds


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="全国医院公开信息采集系统 MVP")
    p.add_argument("--input", type=Path, default=DATA_DIR / "seeds.csv", help="种子 CSV/JSON 路径")
    p.add_argument("--limit", type=int, default=0, help="最多处理几家医院，0 表示不限制")
    p.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite 路径")
    p.add_argument("--no-robots", action="store_true", help="不遵守 robots.txt（仅调试，生产勿用）")
    p.add_argument("--no-export", action="store_true", help="运行结束不导出 CSV/JSON")
    p.add_argument("--log-level", default="INFO", help="日志级别 DEBUG/INFO/WARNING")
    return p.parse_args()


async def _run(args: argparse.Namespace) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sync_init_db(args.db)
    seeds = load_seeds(args.input)
    lim = args.limit if args.limit and args.limit > 0 else None
    seeds = iter_limited(seeds, lim)
    logger.info("加载种子 {} 条", len(seeds))
    respect = not args.no_robots
    async with CrawlPipeline(args.db, respect_robots=respect) as pipe:
        for s in seeds:
            try:
                await pipe.run_seed(s)
            except Exception as e:
                logger.exception("种子处理异常 {}: {}", s.name, e)
    if not args.no_export:
        csv_p, json_p = export_sqlite(args.db, EXPORT_DIR)
        logger.info("已导出: {} , {}", csv_p, json_p)


def main() -> None:
    args = parse_args()
    logger.remove()
    logger.add(sys.stderr, level=args.log_level)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
