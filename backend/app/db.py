"""SQLite storage for local development. Swap for PostgreSQL in production
(the schema is plain SQL and ports directly)."""
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    source_id TEXT NOT NULL,
    source_name TEXT NOT NULL,
    owner TEXT NOT NULL,
    bias TEXT NOT NULL,
    lang TEXT NOT NULL,
    title TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    author TEXT,
    image_url TEXT,
    published_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    category_hint TEXT,
    story_id INTEGER REFERENCES stories(id)
);
CREATE INDEX IF NOT EXISTS idx_articles_story ON articles(story_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub ON articles(published_at);

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lang TEXT NOT NULL,
    headline TEXT,
    summary TEXT,
    summary_by TEXT,            -- 'ai', 'excerpt', 'editor'
    category TEXT NOT NULL DEFAULT 'canada',
    provinces TEXT NOT NULL DEFAULT '',   -- comma-separated codes, e.g. 'ON,QC'
    lead_article_id INTEGER,
    status TEXT NOT NULL DEFAULT 'draft', -- draft | review | published | rejected
    is_top INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    needs_resummary INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_stories_status ON stories(status, lang);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session(path: str | None = None):
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
