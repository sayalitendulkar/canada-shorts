"""Fetch RSS/Atom feeds and store new articles. Only feed content is used:
no scraping of article pages, nothing behind paywalls."""
import json
import logging
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from . import config
from .text import strip_html

log = logging.getLogger(__name__)


def load_sources(path: str | None = None) -> list[dict]:
    with open(path or config.SOURCES_FILE, encoding="utf-8") as f:
        return json.load(f)["sources"]


def _when(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    for key in ("published", "updated"):
        if entry.get(key):
            try:
                return parsedate_to_datetime(entry[key]).astimezone(timezone.utc)
            except (TypeError, ValueError):
                pass
    return datetime.now(timezone.utc)


def _image(entry) -> str | None:
    for key in ("media_content", "media_thumbnail"):
        items = entry.get(key) or []
        for it in items:
            if it.get("url"):
                return it["url"]
    for link in entry.get("links", []):
        if link.get("rel") == "enclosure" and str(link.get("type", "")).startswith("image"):
            return link.get("href")
    return None


def is_not_news(url: str, title: str) -> bool:
    """Ads, sponsored shopping posts and opinion columns are left out."""
    u, t = url.lower(), title.lower().strip()
    return any(p in u for p in config.SKIP_URL_PARTS) or any(t.startswith(p) for p in config.SKIP_TITLE_STARTS)


def parse_feed(raw: bytes | str, source: dict) -> list[dict]:
    """Turn feed XML into article dicts. Pure function, easy to test."""
    feed = feedparser.parse(raw)
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    oldest = now_dt - timedelta(days=config.MAX_ARTICLE_AGE_DAYS)
    out = []
    for e in feed.entries:
        url = e.get("link")
        title = strip_html(e.get("title"))
        if not url or not title or is_not_news(url, title):
            continue
        if _when(e) < oldest:
            continue
        excerpt = strip_html(e.get("summary") or e.get("description") or "")
        out.append(
            {
                "url": url,
                "source_id": source["id"],
                "source_name": source["name"],
                "owner": source["owner"],
                "bias": source["bias"],
                "lang": source["lang"],
                "title": title,
                "excerpt": excerpt[:2000],
                "author": strip_html(e.get("author")) or None,
                "image_url": _image(e),
                "published_at": _when(e).isoformat(),
                "fetched_at": now,
                "category_hint": source.get("category"),
            }
        )
    return out


def save_articles(conn, articles: list[dict]) -> int:
    cols = list(articles[0].keys()) if articles else []
    added = 0
    for a in articles:
        cur = conn.execute(
            f"INSERT OR IGNORE INTO articles ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [a[c] for c in cols],
        )
        added += cur.rowcount
    return added


def fetch_all(conn, sources: list[dict] | None = None) -> int:
    sources = sources or load_sources()
    total = 0
    headers = {"User-Agent": config.USER_AGENT}
    with httpx.Client(timeout=config.FETCH_TIMEOUT_S, headers=headers, follow_redirects=True) as client:
        for s in sources:
            try:
                r = client.get(s["url"])
                r.raise_for_status()
                total += save_articles(conn, parse_feed(r.content, s))
            except Exception as exc:  # one bad feed must not stop the run
                log.warning("feed %s failed: %s", s["id"], exc)
    return total
