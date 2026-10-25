"""Public API for the app + a minimal editor review console.

Run:  uvicorn app.api:app --reload
Docs: http://localhost:8000/docs
"""
from datetime import datetime, timezone
from math import exp

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field

from . import config
from .categorize import CATEGORIES, LABELS
from .cluster import bias_mix
from .db import connect

app = FastAPI(title="Canada Shorts API", version="0.1.0")


def get_conn():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def require_admin(x_admin_token: str = Header(default="")):
    if x_admin_token != config.ADMIN_TOKEN:
        raise HTTPException(401, "admin token required")


# ---------- shaping ----------

def story_out(conn, s) -> dict:
    arts = conn.execute(
        "SELECT * FROM articles WHERE story_id = ? ORDER BY published_at", (s["id"],)
    ).fetchall()
    lead = next((a for a in arts if a["id"] == s["lead_article_id"]), arts[0] if arts else None)
    image = next((a["image_url"] for a in arts if a["image_url"]), None)
    seen, sources = set(), []
    for a in arts:
        if a["source_name"] in seen:
            continue
        seen.add(a["source_name"])
        sources.append({"name": a["source_name"], "url": a["url"], "bias": a["bias"],
                        "author": a["author"], "published_at": a["published_at"]})
    return {
        "id": s["id"],
        "lang": s["lang"],
        "headline": s["headline"],
        "summary": s["summary"],
        "summary_by": s["summary_by"],
        "category": s["category"],
        "provinces": [p for p in s["provinces"].split(",") if p],
        "is_top": bool(s["is_top"]),
        "image_url": image,
        "lead_source": sources[0]["name"] if sources else None,
        "read_more_url": lead["url"] if lead else None,
        "published_at": lead["published_at"] if lead else s["created_at"],
        "sources": sources,
        "bias": bias_mix(arts),
        "owners": sorted({a["owner"] for a in arts}),
    }


def score(story: dict, province: str | None, now: datetime) -> float:
    age_h = (now - datetime.fromisoformat(story["published_at"])).total_seconds() / 3600
    freshness = exp(-max(age_h, 0) / 12)
    # Covered by several outlets = major news, so it ranks well above single-outlet items.
    importance = 1 + min(story["bias"]["total"] - 1, 6) * 0.6 + (1.5 if story["is_top"] else 0)
    local = 1.4 if province and province in story["provinces"] else 1.0
    return freshness * importance * local


def apply_diversity(stories: list[dict], limit: int) -> list[dict]:
    """Owner cap (~25% of the page) and no more than 3 in a row of one category."""
    cap = max(1, int(limit * config.OWNER_CAP_SHARE))
    owner_count: dict[str, int] = {}
    out, deferred = [], []
    for s in stories:
        owner = s["owners"][0] if s["owners"] else "?"
        streak = out[-3:]
        if owner_count.get(owner, 0) >= cap or (len(streak) == 3 and all(x["category"] == s["category"] for x in streak)):
            deferred.append(s)
            continue
        owner_count[owner] = owner_count.get(owner, 0) + 1
        out.append(s)
        if len(out) == limit:
            return out
    return (out + deferred)[:limit]


# ---------- public endpoints ----------

@app.get("/preview", response_class=FileResponse)
def preview():
    """See the feed as phone-style cards in any browser."""
    return FileResponse(config.BASE_DIR / "preview.html", media_type="text/html")


_ICON = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" '
         b'fill="#D52B1E"/><text x="16" y="22" font-family="Arial" font-size="15" font-weight="700" '
         b'fill="#fff" text-anchor="middle">CS</text></svg>')


@app.get("/favicon.ico")
def favicon():
    return Response(_ICON, media_type="image/svg+xml")


@app.get("/waiting")
def waiting(lang: str = Query("en", pattern="^(en|fr)$"), conn=Depends(get_conn)):
    """How many big stories are waiting for an editor (shown on the preview page)."""
    n = conn.execute("SELECT COUNT(*) FROM stories WHERE status = 'review' AND lang = ?", (lang,)).fetchone()[0]
    return {"waiting": n}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/categories")
def categories(lang: str = Query("en", pattern="^(en|fr)$")):
    return [{"id": c, "label": LABELS[lang][c]} for c in CATEGORIES]


@app.get("/feed")
def feed(
    lang: str = Query("en", pattern="^(en|fr)$"),
    category: str | None = None,
    province: str | None = Query(None, pattern="^(ON|QC|BC|AB|MB|SK|NS|NB|NL|PE|YT|NT|NU)$"),
    categories: str | None = Query(None, description="For category=myfeed: the reader's chosen categories, comma-separated"),
    limit: int = Query(30, ge=1, le=100),
    conn=Depends(get_conn),
):
    sql = "SELECT * FROM stories WHERE status = 'published' AND lang = ?"
    args: list = [lang]
    if category in (None, "top"):
        pass  # main feed: every story, ranked by importance and freshness
    elif category == "myfeed":
        chosen = [c for c in (categories or "").split(",") if c in CATEGORIES and c not in ("top", "province")]
        conds = []
        if chosen:
            conds.append(f"category IN ({','.join('?' * len(chosen))})")
            args.extend(chosen)
        if province:  # local news always belongs in My Feed
            conds.append("(',' || provinces || ',') LIKE ?")
            args.append(f"%,{province},%")
        if conds:
            sql += " AND (" + " OR ".join(conds) + ")"
    elif category == "province" and province:
        sql += " AND (',' || provinces || ',') LIKE ?"
        args.append(f"%,{province},%")
    elif category:
        sql += " AND category = ?"
        args.append(category)
    sql += " ORDER BY updated_at DESC LIMIT 400"
    stories = [story_out(conn, s) for s in conn.execute(sql, args).fetchall()]
    now = datetime.now(timezone.utc)
    stories.sort(key=lambda s: score(s, province, now), reverse=True)
    return {"stories": apply_diversity(stories, limit), "generated_at": now.isoformat()}


@app.get("/stories/{story_id}")
def story(story_id: int, conn=Depends(get_conn)):
    s = conn.execute("SELECT * FROM stories WHERE id = ? AND status = 'published'", (story_id,)).fetchone()
    if not s:
        raise HTTPException(404, "not found")
    return story_out(conn, s)


class Report(BaseModel):
    story_id: int
    reason: str = Field(..., min_length=3, max_length=500)


@app.post("/report", status_code=201)
def report(body: Report, conn=Depends(get_conn)):
    """'Report this summary' — required for AI-generated content on Google Play."""
    if not conn.execute("SELECT 1 FROM stories WHERE id = ?", (body.story_id,)).fetchone():
        raise HTTPException(404, "not found")
    conn.execute("INSERT INTO reports (story_id, reason, created_at) VALUES (?, ?, ?)",
                 (body.story_id, body.reason, datetime.now(timezone.utc).isoformat()))
    # Three reports pull a story back into review automatically.
    n = conn.execute("SELECT COUNT(*) FROM reports WHERE story_id = ?", (body.story_id,)).fetchone()[0]
    if n >= 3:
        conn.execute("UPDATE stories SET status = 'review' WHERE id = ?", (body.story_id,))
    return {"ok": True}


# ---------- editor console ----------

class Decision(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    headline: str | None = None
    summary: str | None = None
    is_top: bool | None = None


@app.get("/admin/queue", dependencies=[Depends(require_admin)])
def queue(conn=Depends(get_conn)):
    rows = conn.execute("SELECT * FROM stories WHERE status = 'review' ORDER BY updated_at DESC LIMIT 100").fetchall()
    return [story_out(conn, s) | {"status": s["status"]} for s in rows]


@app.post("/admin/stories/{story_id}", dependencies=[Depends(require_admin)])
def decide(story_id: int, d: Decision, conn=Depends(get_conn)):
    s = conn.execute("SELECT * FROM stories WHERE id = ?", (story_id,)).fetchone()
    if not s:
        raise HTTPException(404, "not found")
    headline = d.headline or s["headline"]
    summary = d.summary or s["summary"]
    if summary and len(summary.split()) > config.MAX_WORDS:
        raise HTTPException(422, f"summary must be {config.MAX_WORDS} words or fewer")
    edited = (d.headline is not None and d.headline != s["headline"]) or (
        d.summary is not None and d.summary != s["summary"])
    conn.execute(
        "UPDATE stories SET status=?, headline=?, summary=?, summary_by=?, is_top=?, updated_at=? WHERE id=?",
        ("published" if d.action == "approve" else "rejected", headline, summary,
         "editor" if edited else s["summary_by"],
         int(d.is_top) if d.is_top is not None else s["is_top"],
         datetime.now(timezone.utc).isoformat(), story_id),
    )
    return {"ok": True}


@app.get("/admin", response_class=HTMLResponse)
def console():
    """Tiny review page. Enter the admin token once; approve, edit or reject."""
    return HTMLResponse(_CONSOLE.replace("{{MAX}}", str(config.MAX_WORDS)))


_CONSOLE = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Canada Shorts — review</title>
<style>body{font:15px system-ui;margin:24px auto;max-width:760px;padding:0 16px}
.card{border:1px solid #ccc;border-radius:8px;padding:12px 16px;margin:12px 0}
textarea,input[type=text]{width:100%;font:inherit;box-sizing:border-box}
.meta{color:#666;font-size:13px}button{margin-right:8px}</style></head><body>
<h1>Review queue</h1><p><input id="tok" type="password" placeholder="admin token"> <button onclick="load()">Load</button></p>
<div id="q"></div>
<script>
const E=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const H=()=>({'Content-Type':'application/json','X-Admin-Token':document.getElementById('tok').value});
async function load(){const r=await fetch('/admin/queue',{headers:H()});if(!r.ok){alert('token?');return}
const items=await r.json();const q=document.getElementById('q');q.innerHTML=items.length?'':'<p>Queue empty.</p>';
for(const s of items){const d=document.createElement('div');d.className='card';
d.innerHTML=`<div class=meta>#${s.id} · ${E(s.lang).toUpperCase()} · ${E(s.category)} · ${s.bias.total} outlets (L${s.bias.left}/C${s.bias.centre}/R${s.bias.right}) · by ${E(s.summary_by)}</div>
<input type=text value="" class=h><textarea rows=4 class=s></textarea><div class=meta>max {{MAX}} words</div>
<div class=meta>${s.sources.map(x=>`<a href="${E(x.url)}" target=_blank rel=noopener>${E(x.name)}</a>`).join(' · ')}</div>
<p><label><input type=checkbox class=t ${s.is_top?'checked':''}> Top story</label></p>
<button class=a>Approve</button><button class=r>Reject</button>`;
d.querySelector('.h').value=s.headline||'';d.querySelector('.s').value=s.summary||'';
const send=async(action)=>{await fetch('/admin/stories/'+s.id,{method:'POST',headers:H(),body:JSON.stringify({action,
headline:d.querySelector('.h').value,summary:d.querySelector('.s').value,is_top:d.querySelector('.t').checked})});d.remove()};
d.querySelector('.a').onclick=()=>send('approve');d.querySelector('.r').onclick=()=>send('reject');q.appendChild(d)}}
</script></body></html>"""
