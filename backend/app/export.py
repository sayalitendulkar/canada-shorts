"""Write the news as ready-made files for the app and the online preview.

    python -m app.export site

Creates:  site/index.html (the preview), site/data/feed_en.json, feed_fr.json,
categories_en.json, categories_fr.json. Upload the folder anywhere (GitHub Pages,
Cloudflare Pages, Hostinger) — no server program needed to read it."""
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config
from .api import score, story_out
from .categorize import CATEGORIES, LABELS
from .db import session

MAX_AGE_HOURS = 72
MAX_STORIES = 300


def export(out_dir: str) -> dict:
    out = Path(out_dir)
    data = out / "data"
    data.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=MAX_AGE_HOURS)).isoformat()
    counts = {}
    with session() as conn:
        for lang in ("en", "fr"):
            rows = conn.execute(
                """SELECT s.* FROM stories s WHERE s.status = 'published' AND s.lang = ?
                   AND EXISTS (SELECT 1 FROM articles a WHERE a.story_id = s.id AND a.published_at >= ?)""",
                (lang, since),
            ).fetchall()
            stories = [story_out(conn, r) for r in rows]
            for st in stories:
                st["rank"] = round(score(st, None, now), 4)
            stories.sort(key=lambda st: st["rank"], reverse=True)
            stories = stories[:MAX_STORIES]
            (data / f"feed_{lang}.json").write_text(
                json.dumps({"generated_at": now.isoformat(), "stories": stories}, ensure_ascii=False), encoding="utf-8")
            (data / f"categories_{lang}.json").write_text(
                json.dumps([{"id": c, "label": LABELS[lang][c]} for c in CATEGORIES], ensure_ascii=False), encoding="utf-8")
            counts[lang] = len(stories)
    html = (config.BASE_DIR / "preview.html").read_text(encoding="utf-8")
    html = html.replace("<script>", "<script>window.CS_STATIC = true;</script>\n<script>", 1)
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return counts


if __name__ == "__main__":
    print(export(sys.argv[1] if len(sys.argv) > 1 else "site"))
