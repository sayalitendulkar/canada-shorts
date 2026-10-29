"""One pipeline run: fetch -> cluster -> categorise -> summarise -> publish or queue.
Schedule it every 10 minutes (cron, systemd timer, or Cloud Scheduler):

    python -m app.pipeline
"""
import json
import logging
import time
from datetime import datetime, timedelta, timezone

from . import config
from .categorize import categorize, provinces
from .cluster import assign_stories
from .db import session
from .article import fetch_article_text
from .gemini import QuotaExceeded
from .ingest import fetch_all, load_sources
from .summarize import ai_enabled, summarize, summarize_batch

log = logging.getLogger(__name__)


def _ai_used_today(conn) -> dict[str, int]:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    used = {}
    for lang in ("en", "fr"):
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (f"ai_count_{lang}_{day}",)).fetchone()
        used[lang] = int(row["value"]) if row else 0
    return used


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
    stats = {"published": 0, "review": 0, "ai_written": 0, "ai_requests": 0, "ai_wanted": 0,
             "ai_failed_checks": 0, "ai_too_short": 0, "ai_error": ""}
    # Stories with new articles, plus recent stories that still show the outlet's own
    # text (so they get an AI summary as soon as there is free quota).
    since = (datetime.now(timezone.utc) - timedelta(hours=config.AI_MAX_AGE_HOURS)).isoformat()
    rows = conn.execute(
        """SELECT * FROM stories WHERE status != 'rejected' AND (needs_resummary = 1
           OR (summary_by = 'excerpt' AND created_at >= ?))""", (since,)
    ).fetchall()
    # Article pages we don't open for AI: paywalled sites, and sites that ask AI tools not to read them.
    paywalled = {s["id"] for s in load_sources() if s.get("paywall") or s.get("no_ai_read")}
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

    used = _ai_used_today(conn)  # requests used today, per language
    ai_blocked = not ai_enabled()
    ai_results: dict[int, dict] = {}
    waiting: set[int] = set()  # fresh stories that still need an AI summary later

    row = conn.execute("SELECT value FROM meta WHERE key = 'ai_skip'").fetchone()
    skip_ids: set[int] = set(json.loads(row["value"])) if row else set()

    # 1) Pick the stories that should get an AI summary, biggest news first.
    queue: dict[str, list] = {"en": [], "fr": []}
    for story, arts, n_outlets in work:
        lead = arts[0]
        fresh = (now - datetime.fromisoformat(lead["published_at"])).total_seconds() < config.AI_MAX_AGE_HOURS * 3600
        if story["summary_by"] == "editor" or not fresh or not ai_enabled():
            continue
        if story["id"] in skip_ids and not story["needs_resummary"]:
            continue  # too little text last time and nothing new since
        words = sum(len(f"{a['title']} {a['excerpt']}".split()) for a in arts)
        queue[story["lang"]].append((story, arts, words))
    stats["ai_wanted"] = sum(len(v) for v in queue.values())
    for lang in queue:  # stories without any AI text go first; AI updates of known stories after
        queue[lang].sort(key=lambda it: it[0]["summary_by"] == "ai")

    # 2) Ask the AI for several stories per request.
    run_requests = {"en": 0, "fr": 0}

    def send(lang, batch):
        nonlocal ai_blocked
        try:
            used[lang] += 1
            run_requests[lang] += 1
            stats["ai_requests"] += 1
            results = summarize_batch(batch, lang)
            ai_results.update(results)
            stats["ai_written"] += sum(r["summary_by"] == "ai" for r in results.values())
            stats["ai_failed_checks"] += sum("ai_draft_failed_checks" in r["problems"] for r in results.values())
            waiting.update(k for k, r in results.items() if r["summary_by"] != "ai" and "ai_draft_failed_checks" not in r["problems"])
            time.sleep(config.AI_PAUSE_SECONDS)  # stay under per-minute limits
        except QuotaExceeded as exc:
            log.warning("AI free limit reached; will retry on a later run. Google says: %s", exc)
            stats["ai_error"] = "quota: " + str(exc)[:300]
            ai_blocked = True
            waiting.update(k for k, _, _ in batch)

    for lang, items in queue.items():
        # Each language gets its own share of this run's requests, so French isn't starved.
        run_cap = max(1, round(config.AI_MAX_REQUESTS_PER_RUN * (config.AI_FRENCH_SHARE if lang == "fr" else 1 - config.AI_FRENCH_SHARE)))
        batch = []
        for story, arts, words in items:
            if ai_blocked or used[lang] >= config.ai_limit(lang) or run_requests[lang] >= run_cap:
                waiting.add(story["id"])
                continue
            full = _readable_text(arts, paywalled)
            if not full and words < 40:
                skip_ids.add(story["id"])  # only a one-line teaser: not enough to summarise honestly
                stats["ai_too_short"] += 1
                continue
            batch.append((story["id"], arts, full))
            if len(batch) == config.AI_BATCH_SIZE:  # fill each request before sending it
                send(lang, batch)
                batch = []
        if batch and not ai_blocked:
            send(lang, batch)
        elif batch:
            waiting.update(k for k, _, _ in batch)
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('ai_skip', ?)",
                 (json.dumps(sorted(skip_ids)[-3000:]),))

    # 3) Save every story.
    for story, arts, n_outlets in work:
        lead = arts[0]  # newest article: freshest headline and facts
        all_text = " ".join(f"{a['title']} {a['excerpt']}" for a in arts)
        retry_later = story["id"] in waiting
        if story["summary_by"] == "editor":  # an editor's version always wins
            result = {"headline": story["headline"], "summary": story["summary"], "summary_by": "editor", "problems": []}
        elif story["id"] in ai_results and ai_results[story["id"]]["summary_by"] == "ai":
            result = ai_results[story["id"]]
        elif story["summary_by"] == "ai":  # keep the AI text we already have
            result = {"headline": story["headline"], "summary": story["summary"], "summary_by": "ai", "problems": []}
        else:
            result = ai_results.get(story["id"]) or summarize(arts, story["lang"], use_ai=False)

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
    day = now.strftime("%Y-%m-%d")
    for lang, n in used.items():
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (f"ai_count_{lang}_{day}", str(n)))
    return stats


def run_once(fetch: bool = True) -> dict:
    with session() as conn:
        added = fetch_all(conn) if fetch else 0
        clustered = assign_stories(conn)
        stats = process_stories(conn)
        stats.update({"new_articles": added, "clustered": clustered,
                      "ai_used_today": _ai_used_today(conn), "finished_at": datetime.now(timezone.utc).isoformat()})
        from . import summarize as _s
        if not stats["ai_error"] and _s.last_error:
            stats["ai_error"] = _s.last_error
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('last_run', ?)", (json.dumps(stats),))
    log.info("pipeline run: %s", stats)
    return stats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_once())
