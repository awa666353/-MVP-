-- 全国医院公开信息采集系统 - SQLite Schema（可迁移至 PostgreSQL）

PRAGMA foreign_keys = ON;

-- 医院主表
CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT DEFAULT '',
    level TEXT DEFAULT '',
    nature TEXT DEFAULT '',
    province TEXT DEFAULT '',
    city TEXT DEFAULT '',
    address TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    postal_code TEXT DEFAULT '',
    website_url TEXT NOT NULL,
    introduction TEXT DEFAULT '',
    registration_entry_url TEXT DEFAULT '',
    outpatient_hours TEXT DEFAULT '',
    visit_notes TEXT DEFAULT '',
    supports_appointment INTEGER, -- NULL unknown, 0/1
    latitude REAL,
    longitude REAL,
    featured_tech TEXT DEFAULT '',
    expert_team_url TEXT DEFAULT '',
    branch_campus_info TEXT DEFAULT '',
    emergency_info TEXT DEFAULT '',
    internet_hospital_info TEXT DEFAULT '',
    confidence_score REAL DEFAULT 0,
    review_flags TEXT DEFAULT '[]', -- JSON array string
    adapter_id TEXT DEFAULT 'generic',
    last_crawled_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_hospitals_website
    ON hospitals(website_url);

CREATE INDEX IF NOT EXISTS ix_hospitals_province_city ON hospitals(province, city);
CREATE INDEX IF NOT EXISTS ix_hospitals_name ON hospitals(name);

-- 科室 / 重点专科
CREATE TABLE IF NOT EXISTS hospital_departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    description TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    raw_snippet TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_dept_hospital ON hospital_departments(hospital_id);

-- 挂号方式
CREATE TABLE IF NOT EXISTS hospital_registration_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    method_code TEXT NOT NULL,
    method_label_zh TEXT DEFAULT '',
    detail_text TEXT DEFAULT '',
    booking_url TEXT DEFAULT '',
    supports_booking INTEGER,
    source_url TEXT DEFAULT '',
    raw_snippet TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_reg_hospital ON hospital_registration_methods(hospital_id);

-- 字段级来源页面（可多条）
CREATE TABLE IF NOT EXISTS hospital_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    page_title TEXT DEFAULT '',
    fetched_at TEXT NOT NULL,
    updated_at_page TEXT,
    raw_snippet TEXT DEFAULT '',
    confidence REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_src_hospital ON hospital_sources(hospital_id);

-- 抓取任务 / 日志
CREATE TABLE IF NOT EXISTS crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_seed_name TEXT,
    target_url TEXT NOT NULL,
    status TEXT NOT NULL, -- success / error / skipped_robots / timeout
    message TEXT DEFAULT '',
    started_at TEXT,
    finished_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_crawl_url ON crawl_logs(target_url);

-- 原始页面
CREATE TABLE IF NOT EXISTS raw_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER REFERENCES hospitals(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    final_url TEXT DEFAULT '',
    http_status INTEGER DEFAULT 0,
    content_type TEXT DEFAULT '',
    title TEXT DEFAULT '',
    html_sha256 TEXT DEFAULT '',
    text_preview TEXT DEFAULT '',
    fetched_at TEXT NOT NULL,
    crawl_log_id INTEGER REFERENCES crawl_logs(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_raw_hospital ON raw_pages(hospital_id);
CREATE INDEX IF NOT EXISTS ix_raw_url ON raw_pages(url);

-- URL 去重：已成功抓取的 URL（增量更新）
CREATE TABLE IF NOT EXISTS fetched_url_cache (
    url TEXT PRIMARY KEY,
    html_sha256 TEXT,
    fetched_at TEXT NOT NULL
);
