"""Group articles about the same event into one story (one card).

Method: TF-IDF word vectors (headline words count double), compared with each
recent story's centre; same language, within a 36-hour window. Tuned on real
Canadian feeds (Oct 2026). Upgrade path: sentence embeddings + cross-language
matching so an English and French story can share one bias bar."""
import math
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import config
from .ingest import is_not_news
from .text import keywords

Vector = dict[str, float]


def _terms(row) -> Counter:
    """Headline words count twice; the first 30 words of the excerpt add context."""
    title = list(keywords(row["title"]))
    body = list(keywords(" ".join(row["excerpt"].split()[:30])))
    return Counter(title * 2 + body)


def _tfidf(counts: list[Counter]) -> list[Vector]:
    df = Counter(w for c in counts for w in c)
    n = len(counts)
    out = []
    for c in counts:
        v = {w: tf * math.log((n + 1) / (df[w] + 1)) for w, tf in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        out.append({w: x / norm for w, x in v.items()})
    return out


def cosine(a: Vector, b: Vector) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())


def _centroid(vectors: list[Vector]) -> Vector:
    total: Counter = Counter()
    for v in vectors:
        for w, x in v.items():
            total[w] += x
    norm = math.sqrt(sum(x * x for x in total.values())) or 1.0
    return {w: x / norm for w, x in total.items()}


def _ts(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def housekeeping(conn) -> None:
    """Drop old or non-news articles, and regroup everything when the grouping
    method has changed (CLUSTER_VERSION)."""
    now = datetime.now(timezone.utc)
    # Fix times that are in the future (feeds with a wrong time zone).
    conn.execute("UPDATE articles SET published_at = ? WHERE published_at > ?",
                 (now.isoformat(), (now + timedelta(minutes=5)).isoformat()))
    cutoff = (now - timedelta(days=7)).isoformat()
    conn.execute("DELETE FROM articles WHERE published_at < ?", (cutoff,))
    for row in conn.execute("SELECT id, url, title FROM articles").fetchall():
        if is_not_news(row["url"], row["title"]):
            conn.execute("DELETE FROM articles WHERE id = ?", (row["id"],))
    ver = conn.execute("SELECT value FROM meta WHERE key = 'cluster_version'").fetchone()
    if ver is None or int(ver["value"]) != config.CLUSTER_VERSION:
        conn.execute("UPDATE articles SET story_id = NULL")
        conn.execute("DELETE FROM reports")
        conn.execute("DELETE FROM stories")
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('cluster_version', ?)",
                     (str(config.CLUSTER_VERSION),))
    conn.execute("DELETE FROM stories WHERE id NOT IN (SELECT DISTINCT story_id FROM articles WHERE story_id IS NOT NULL)")


def assign_stories(conn) -> int:
    """Attach every ungrouped article to the most similar recent story in the
    same language (TF-IDF cosine against the story's centre), or start a new
    story. Returns the number of articles assigned."""
    housekeeping(conn)
    window = config.CLUSTER_WINDOW_HOURS * 3600
    since = (datetime.now(timezone.utc) - timedelta(hours=config.CLUSTER_WINDOW_HOURS * 2)).isoformat()
    rows = conn.execute(
        "SELECT * FROM articles WHERE story_id IS NULL OR published_at >= ? ORDER BY published_at", (since,)
    ).fetchall()
    if not rows:
        return 0
    vecs = dict(zip((r["id"] for r in rows), _tfidf([_terms(r) for r in rows])))

    # story_id -> {lang, members (vectors), last article time}
    stories: dict[int, dict] = {}
    for r in rows:
        if r["story_id"] is None:
            continue
        st = stories.setdefault(r["story_id"], {"lang": r["lang"], "vecs": [], "last": 0.0})
        st["vecs"].append(vecs[r["id"]])
        st["last"] = max(st["last"], _ts(r["published_at"]))
    centroids = {sid: _centroid(st["vecs"]) for sid, st in stories.items()}

    stamp = datetime.now(timezone.utc).isoformat()
    assigned = 0
    for art in rows:
        if art["story_id"] is not None:
            continue
        v, when = vecs[art["id"]], _ts(art["published_at"])
        best_id, best_sim = None, 0.0
        for sid, st in stories.items():
            if st["lang"] != art["lang"] or abs(when - st["last"]) > window:
                continue
            sim = cosine(v, centroids[sid])
            if sim > best_sim:
                best_id, best_sim = sid, sim
        if best_id is not None and best_sim >= config.CLUSTER_THRESHOLD:
            sid = best_id
            conn.execute("UPDATE stories SET needs_resummary = 1, updated_at = ? WHERE id = ?", (stamp, sid))
        else:
            cur = conn.execute(
                "INSERT INTO stories (lang, lead_article_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (art["lang"], art["id"], stamp, stamp),
            )
            sid = cur.lastrowid
            stories[sid] = {"lang": art["lang"], "vecs": [], "last": 0.0}
        conn.execute("UPDATE articles SET story_id = ? WHERE id = ?", (sid, art["id"]))
        st = stories[sid]
        st["vecs"].append(v)
        st["last"] = max(st["last"], when)
        centroids[sid] = _centroid(st["vecs"])
        assigned += 1
    return assigned


BIAS_BUCKETS = ("left", "lean_left", "centre", "lean_right", "right")


def bias_mix(articles) -> dict:
    """Count distinct outlets per side. 'official' sources (government) are
    reported separately and never counted as a side."""
    seen: dict[str, str] = {}
    for a in articles:
        seen.setdefault(a["source_name"], a["bias"])
    mix = {"left": 0, "centre": 0, "right": 0, "official": 0}
    for bias in seen.values():
        if bias in ("left", "lean_left"):
            mix["left"] += 1
        elif bias in ("right", "lean_right"):
            mix["right"] += 1
        elif bias == "official":
            mix["official"] += 1
        elif bias == "unrated":  # not yet rated: counted in the total only, never as a side
            pass
        else:
            mix["centre"] += 1
    mix["total"] = len(seen)
    sides = mix["left"] + mix["centre"] + mix["right"]
    # Blindspot: 3+ outlets and two-thirds or more from one side.
    mix["blindspot"] = None
    if sides >= 3:
        if mix["left"] / sides >= 2 / 3:
            mix["blindspot"] = "mostly_left"
        elif mix["right"] / sides >= 2 / 3:
            mix["blindspot"] = "mostly_right"
    return mix
