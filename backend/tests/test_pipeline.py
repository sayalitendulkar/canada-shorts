"""Offline tests: sample feeds -> clustering -> summaries -> API."""
import os
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

NOW = datetime.now(timezone.utc)


def rss(items):
    body = "".join(
        f"""<item><title>{t}</title><link>{u}</link><description>{d}</description>
        <pubDate>{format_datetime(NOW - timedelta(hours=h))}</pubDate></item>"""
        for t, u, d, h in items
    )
    return f'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title>{body}</channel></rss>'


SRC = {
    "cbc": {"id": "cbc", "name": "CBC News", "owner": "CBC/Radio-Canada", "lang": "en", "bias": "lean_left", "category": "canada"},
    "ctv": {"id": "ctv", "name": "CTV News", "owner": "Bell Media", "lang": "en", "bias": "centre", "category": "canada"},
    "np": {"id": "np", "name": "National Post", "owner": "Postmedia", "lang": "en", "bias": "lean_right", "category": "canada"},
    "lp": {"id": "lp", "name": "La Presse", "owner": "La Presse", "lang": "fr", "bias": "lean_left", "category": "canada"},
}

RATE = "The Bank of Canada cut its key interest rate to 2.25 per cent on Wednesday, citing slower growth and weaker hiring across Canada."


@pytest.fixture()
def env(monkeypatch):
    tmp = tempfile.mkdtemp()
    db = os.path.join(tmp, "t.db")
    from app import config
    monkeypatch.setattr(config, "DB_PATH", db)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    from app.db import session
    from app.ingest import parse_feed, save_articles
    with session() as conn:
        save_articles(conn, parse_feed(rss([
            ("Bank of Canada cuts key interest rate to 2.25%", "https://cbc.ca/a1", RATE, 1),
            ("Wildfire forces evacuation near Kelowna, B.C.", "https://cbc.ca/a2", "Residents of West Kelowna in British Columbia were told to leave as a wildfire grew to 900 hectares.", 3),
        ]), SRC["cbc"]))
        save_articles(conn, parse_feed(rss([
            ("Bank of Canada cuts interest rate to 2.25 per cent", "https://ctv.ca/b1", RATE, 2),
            ("Maple Leafs beat Canadiens 4-2 in NHL opener", "https://ctv.ca/b2", "Toronto Maple Leafs beat the Montreal Canadiens 4-2 at Scotiabank Arena in the NHL season opener.", 5),
        ]), SRC["ctv"]))
        save_articles(conn, parse_feed(rss([
            ("Bank of Canada cuts key rate to 2.25 per cent as growth slows", "https://np.ca/c1", RATE, 1),
        ]), SRC["np"]))
        save_articles(conn, parse_feed(rss([
            ("La Banque du Canada abaisse son taux directeur à 2,25 %", "https://lapresse.ca/d1",
             "La Banque du Canada a abaissé mercredi son taux directeur à 2,25 %, invoquant une croissance plus lente.", 1),
        ]), SRC["lp"]))
    return db


def test_parse_feed_strips_html():
    from app.ingest import parse_feed
    arts = parse_feed(rss([("<b>Hello</b> &amp; bye", "https://x/1", "<p>Body <i>text</i></p>", 0)]), SRC["cbc"])
    assert arts[0]["title"] == "Hello & bye"
    assert arts[0]["excerpt"] == "Body text"


def test_pipeline_clusters_and_routes(env):
    from app.pipeline import run_once
    from app.db import session
    stats = run_once(fetch=False)
    assert stats["clustered"] == 6
    with session() as conn:
        stories = conn.execute("SELECT * FROM stories").fetchall()
        # 3 English rate articles -> 1 story; wildfire; hockey; French rate story
        assert len(stories) == 4
        rate = [s for s in stories if s["lang"] == "en" and "Bank" in s["headline"]][0]
        assert rate["status"] == "review"  # 3 outlets -> top story -> editor approves
        assert rate["category"] == "business"
        hockey = [s for s in stories if "Leafs" in s["headline"]][0]
        assert hockey["category"] == "sports" and hockey["status"] == "published"
        assert "ON" in hockey["provinces"] and "QC" in hockey["provinces"]
        fire = [s for s in stories if "Wildfire" in s["headline"]][0]
        assert fire["category"] == "climate" and fire["provinces"] == "BC"


def test_summary_checks():
    from app.summarize import check_summary
    arts = [{"title": "Rate cut to 2.25%", "excerpt": RATE}]
    assert check_summary("The Bank of Canada cut its rate to 2.25 per cent.", "Rate cut", arts, "en") == []
    probs = check_summary("Bank slams markets with shocking 3.5 per cent cut.", "Rate", arts, "en")
    assert "loaded_word:slams" in probs and "unsupported_number:3.5" in probs
    assert check_summary("word " * 61, "h", arts, "en")[0].startswith("too_long")


def test_bias_mix_and_blindspot():
    from app.cluster import bias_mix
    arts = [{"source_name": n, "bias": b} for n, b in [("A", "lean_left"), ("B", "left"), ("C", "lean_left"), ("D", "centre")]]
    mix = bias_mix(arts)
    assert (mix["left"], mix["centre"], mix["right"], mix["total"]) == (3, 1, 0, 4)
    assert mix["blindspot"] == "mostly_left"


def test_api_feed_review_and_report(env):
    from fastapi.testclient import TestClient
    from app import config
    from app.api import app
    from app.pipeline import run_once
    run_once(fetch=False)
    c = TestClient(app)
    feed = c.get("/feed?lang=en").json()["stories"]
    assert {s["category"] for s in feed} == {"sports", "climate"}  # rate story waits for editor
    assert all(len(s["summary"].split()) <= 60 for s in feed)
    assert c.get("/feed?lang=fr").json()["stories"][0]["lang"] == "fr"
    assert c.get("/feed?lang=en&category=province&province=BC").json()["stories"][0]["provinces"] == ["BC"]

    assert c.get("/admin/queue").status_code == 401
    h = {"X-Admin-Token": config.ADMIN_TOKEN}
    q = c.get("/admin/queue", headers=h).json()
    rate = [s for s in q if s["lang"] == "en"][0]
    assert rate["bias"] == {"left": 1, "centre": 1, "right": 1, "official": 0, "total": 3, "blindspot": None}
    r = c.post(f"/admin/stories/{rate['id']}", headers=h, json={
        "action": "approve", "headline": "Bank of Canada cuts key rate to 2.25%",
        "summary": "The Bank of Canada lowered its key interest rate to 2.25 per cent on Wednesday, citing slower growth and weaker hiring."})
    assert r.status_code == 200
    top = c.get("/feed?lang=en&category=top").json()["stories"]
    assert top[0]["summary_by"] == "editor" and len(top[0]["sources"]) == 3  # big approved story ranks first

    assert c.post("/report", json={"story_id": top[0]["id"], "reason": "wrong number"}).status_code == 201
    assert c.get("/categories?lang=fr").json()[0]["label"] == "À la une"


def test_ads_opinion_and_old_items_skipped():
    from app.ingest import is_not_news, parse_feed
    assert is_not_news("https://globalnews.ca/the-curator/123/walmart/", "The Curator: Deck your halls")
    assert is_not_news("https://nationalpost.com/opinion/x", "Colby Cosh: Smith won")
    assert not is_not_news("https://globalnews.ca/news/1/leafs/", "Leafs scorch Oilers")
    arts = parse_feed(rss([("Old news", "https://x/old", "old", 24 * 10), ("New news", "https://x/new", "new", 1)]), SRC["cbc"])
    assert [a["title"] for a in arts] == ["New news"]


def test_preview_and_icon(env):
    from fastapi.testclient import TestClient
    from app.api import app
    c = TestClient(app)
    r = c.get("/preview")
    assert r.status_code == 200 and "Canada <span>Shorts</span>" in r.text
    assert c.get("/favicon.ico").status_code == 200
    assert c.get("/waiting?lang=en").json() == {"waiting": 0}


def test_my_feed_uses_chosen_categories(env):
    from fastapi.testclient import TestClient
    from app.api import app
    from app.pipeline import run_once
    run_once(fetch=False)
    c = TestClient(app)
    sports = c.get("/feed?lang=en&category=myfeed&categories=sports").json()["stories"]
    assert sports and {s["category"] for s in sports} == {"sports"}
    local = c.get("/feed?lang=en&category=myfeed&categories=sports&province=BC").json()["stories"]
    assert {s["category"] for s in local} == {"sports", "climate"}  # BC wildfire joins via province


def test_pick_gemini_model():
    from app.gemini import pick_model
    names = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-3.6-flash-lite", "gemini-3.8-flash-lite-preview",
             "gemini-3.8-flash", "gemini-3.1-pro", "text-embedding-004"]
    assert pick_model(names) == "gemini-3.6-flash-lite"
    assert pick_model(["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.8-flash-tts"]) == "gemini-3.8-flash"


def test_extract_article_text():
    from app.article import extract_text
    html = ("<html><nav><p>" + "menu link " * 10 + "</p></nav><article><h1>T</h1>"
            "<p>" + "The council voted to approve the new transit line on Tuesday evening. " * 3 + "</p>"
            "<figure><figcaption><p>" + "Photo caption text that should be ignored here. " * 2 + "</p></figcaption></figure>"
            "<p>" + "Construction is expected to begin next spring and finish by 2029. " * 3 + "</p></article>"
            "<script>var x = 1;</script></html>")
    text = extract_text(html)
    assert text.startswith("The council voted") and "Construction" in text
    assert "menu link" not in text and "caption" not in text and "var x" not in text


def test_ai_summaries_with_quota(env, monkeypatch):
    import re
    from app import config, gemini, pipeline
    from app.db import session
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(config, "AI_PAUSE_SECONDS", 0)
    monkeypatch.setattr(config, "AI_DAILY_LIMIT", 2)  # requests per day: 1 English + 1 French
    monkeypatch.setattr(config, "AI_BATCH_SIZE", 2)
    monkeypatch.setattr(pipeline, "fetch_article_text", lambda url: "Full article text " * 50 + RATE)
    calls = []

    def fake(prompt, max_tokens=600):
        calls.append(prompt)
        n = len(re.findall(r"=== Story \d+ ===", prompt))
        return {"stories": [{"id": i, "headline": "Bank of Canada cuts key rate to 2.25 per cent",
                             "summary": "The Bank of Canada cut its key interest rate to 2.25 per cent on Wednesday, citing slower growth."}
                            for i in range(1, n + 1)]}
    monkeypatch.setattr(gemini, "generate_json", fake)
    stats = pipeline.run_once(fetch=False)
    assert len(calls) == 2 and stats["ai_written"] >= 2  # daily request limit respected, several stories per request
    assert "Article text:" in calls[0] and "=== Story 2 ===" in calls[0]
    with session() as conn:
        rate = conn.execute("SELECT * FROM stories WHERE headline LIKE 'Bank of Canada cuts key rate%' AND lang='en'").fetchone()
        assert rate["summary_by"] == "ai"
        left = conn.execute("SELECT COUNT(*) FROM stories WHERE needs_resummary = 1").fetchone()[0]
        assert left >= 1  # stories that missed out wait for tomorrow's quota

    def over(prompt, max_tokens=600):
        raise gemini.QuotaExceeded("429")
    monkeypatch.setattr(gemini, "generate_json", over)
    monkeypatch.setattr(config, "AI_DAILY_LIMIT", 50)
    pipeline.run_once(fetch=False)  # must not crash; falls back to excerpts
    with session() as conn:
        assert conn.execute("SELECT summary_by FROM stories WHERE id = ?", (rate["id"],)).fetchone()[0] == "ai"


def test_clean_title_and_future_times():
    from app.summarize import clean_title
    assert clean_title("B.C. elects first Conservative government in nearly 100 years. Live updates here.") == \
        "B.C. elects first Conservative government in nearly 100 years"
    assert clean_title("WATCH: Leafs win again | CTV News") == "Leafs win again"
    from app.ingest import _when
    future = (datetime.now(timezone.utc) + timedelta(hours=4)).timetuple()
    assert _when({"published_parsed": future}) <= datetime.now(timezone.utc) + timedelta(seconds=5)


def test_gemini_falls_back_to_next_free_model(monkeypatch):
    import httpx
    from app import config, gemini
    monkeypatch.setattr(config, "GEMINI_API_KEY", "k")
    monkeypatch.setattr(config, "GEMINI_MODEL", "")
    monkeypatch.setattr(gemini, "_queue", None)
    monkeypatch.setattr(gemini, "list_models", lambda: ["gemini-3.6-flash-lite", "gemini-3.6-flash"])
    seen = []

    def post(url, **kw):
        seen.append(url)
        req = httpx.Request("POST", url)
        if "flash-lite" in url:
            return httpx.Response(429, json={"error": {"message": "Quota exceeded ... limit: 0, model: flash-lite"}}, request=req)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"headline": "H", "summary": "S"}'}]}}]}, request=req)
    monkeypatch.setattr(gemini.httpx, "post", post)
    assert gemini.generate_json("x") == {"headline": "H", "summary": "S"}
    assert "flash-lite" in seen[0] and "3.6-flash:" in seen[1]


def test_export_static_site(env, monkeypatch, tmp_path):
    import json
    from app import config
    from app.export import export
    from app.pipeline import run_once
    monkeypatch.setattr(config, "EDITOR_REVIEW", False)
    run_once(fetch=False)
    counts = export(str(tmp_path))
    assert counts["en"] == 3 and counts["fr"] == 1  # big rate story published without an editor
    feed = json.loads((tmp_path / "data" / "feed_en.json").read_text(encoding="utf-8"))
    ranks = [s["rank"] for s in feed["stories"]]
    assert ranks == sorted(ranks, reverse=True) and len(feed["stories"][0]["sources"]) == 3
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "window.CS_STATIC = true" in html
