"""全局配置：并发、超时、抓取深度、User-Agent 等。"""

from pathlib import Path

# 项目根目录（含 hospital_crawler 包的上级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_PATH = DATA_DIR / "hospitals.sqlite"

# HTTP
DEFAULT_USER_AGENT = (
    "HospitalPublicCrawler/0.1 (+https://example.local; research; contact@example.local)"
)
REQUEST_TIMEOUT_SEC = 25.0
MAX_CONCURRENT_REQUESTS = 3
MIN_REQUEST_INTERVAL_SEC = 1.0  # 礼貌间隔，配合 semaphore 使用

# 站内爬取
MAX_CRAWL_DEPTH = 3
MAX_PAGES_PER_HOSPITAL = 40

# robots.txt
RESPECT_ROBOTS_TXT = True

# 置信度阈值（低于此进入待复核）
LOW_CONFIDENCE_THRESHOLD = 0.45

# 导出
EXPORT_DIR = DATA_DIR / "exports"
