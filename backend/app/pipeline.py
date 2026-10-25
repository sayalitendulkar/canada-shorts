"""One pipeline run: fetch -> cluster -> categorise -> summarise -> publish or queue.
Schedule it every 10 minutes (cron, systemd timer, or Cloud Scheduler):

    python -m app.pipeline
"""
import logging
import time
from datetime import datetime, timezone

from . import config
from .categorize import categorize, provinces
from .cluster import assign_stories
from .db import session
from .article import fetch_article_text
from .gemini import QuotaExceeded
from .ingest import fetch_all, load_sources
from .summarize import ai_enabled, summarize

log = logging.getLogger(__name__)


def _ai_used_today(conn) -> tuple[str, int]:
    key = "ai_count_" + datetime.now(timezone.utc).strftime("%Y-%m-%d")
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return key, int(row["value"]) if row else 0


def _readable_text(arts, paywalled: set[str]) -> str:
    """Article text from the newest outlet that isn't paywalled (max 2 tries)."""
    tries = 0
    for a in arts:  # newest first
        if a["source_id"] in paywalled:
            continue
        text = fetch_article_text(a["url"])
        tries += 1
        if len(text.split()) >= 80:
            return text
        if tries >= 2:
            break
    return ""


def process_stories(conn) -> dict:
    stats = {"published": 0, "review": 0, "ai_written": 0}
    rows = conn.execute(
        "SELECT * FROM stories WHERE needs_resummary = 1 AND status != 'rejected'"
    ).fetchall()
    paywalled = {s["id"] for s in load_sources() if s.get("paywall")}
    now = datetime.now(timezone.utc)

    # Most important first (more outlets, then newest) so the free AI quota goes to big news.
    work = []
    for story in rows:
        arts = conn.execute(
            "SELECT * FROM articles WHERE story_id = ? ORDER BY published_at DESC", (story["id"],)
        ).fetchall()
        if arts:
            work.append((story, arts, len({a["source_name"] for a in arts})))
    work.sort(key=lambda w: (w[2], w[1][0]["published_at"]), reverse=True)

    quota_key, used = _ai_used_today(conn)
    ai_blocked = not ai_enabled()
    for story, arts, n_outlets in work:
        lead = arts[0]  # newest article: freshest headline and facts
        all_text = " ".join(f"{a['title']} {a['excerpt']}" for a in arts)
        fresh = (now - datetime.fromisoformat(lead["published_at"])).total_seconds() < config.AI_MAX_AGE_HOURS * 3600
        retry_later = False

        if story["summary_by"] == "editor":  # an editor's version always wins
            result = {"headline": story["headline"], "summary": story["summary"], "summary_by": "editor", "problems": []}
        else:
            result = None
            want_ai = fresh and not ai_blocked and used < config.AI_DAILY_LIMIT
            if want_ai:
                full_text = _readable_text(arts, paywalled)
                excerpt_words = sum(len(a["excerpt"].split()) for a in arts)
                if full_text or excerpt_words >= 80:
                    try:
                        used += 1
                        result = summarize(arts, story["lang"], full_text)
                        if result["summary_by"] == "ai":
                            stats["ai_written"] += 1
                        time.sleep(config.AI_PAUSE_SECONDS)  # stay under per-minute limits
                    except QuotaExceeded as exc:
                        log.warning("AI free limit reached; will retry on a later run. Google says: %s", exc)
                        ai_blocked, retry_later = True, True
            elif fresh and ai_enabled() and story["summary_by"] != "ai":
                retry_later = True  # quota used up for today: try again tomorrow
            if result is None or result["summary_by"] != "ai":
                if story["summary_by"] == "ai":  # keep the AI text we already have
                    result = {"headline": story["headline"], "summary": story["summary"], "summary_by": "ai", "problems": []}
                elif result is None:
                    result = summarize(arts, story["lang"], use_ai=False)

        is_top = n_outlets >= config.TOP_STORY_MIN_SOURCES
        if story["status"] == "published" and story["summary_by"] == "editor":
            status = "published"
        elif config.EDITOR_REVIEW and (is_top or result["problems"]):
            status = "review"  # human approves big or flagged stories
        else:
            status = "published"
        stats["published" if status == "published" else "review"] += 1

        conn.execute(
            """UPDATE stories SET headline=?, summary=?, summary_by=?, category=?, provinces=?,
               lead_article_id=?, status=?, is_top=?, needs_resummary=?, updated_at=? WHERE id=?""",
            (
                result["headline"], result["summary"], result["summary_by"],
                categorize(lead["title"], all_text, lead["category_hint"]),
                ",".join(provinces(all_text)), lead["id"], status, int(is_top), int(retry_later),
                now.isoformat(), story["id"],
            ),
        )
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (quota_key, str(used)))
    return stats


def run_once(fetch: bool = True) -> dict:
    with session() as conn:
        added = fetch_all(conn) if fetch else 0
        clustered = assign_stories(conn)
        stats = process_stories(conn)
    stats.update({"new_articles": added, "clustered": clustered})
    log.info("pipeline run: %s", stats)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_once())
