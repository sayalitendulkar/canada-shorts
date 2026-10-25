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

PRIVACY_HTML = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Privacy policy / Politique de confidentialité — Canada Shorts</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:720px;margin:24px auto;padding:0 16px;color:#1c1c1e}h1{font-size:24px}h2{font-size:18px;margin-top:28px}</style>
</head><body>
<h1>Privacy policy</h1><p><i>Last updated: October 25, 2026</i></p>
<p>Canada Shorts ("the app") shows short summaries of Canadian news with links to the original publishers.</p>
<h2>What we collect</h2>
<p>We do not ask you to create an account and we do not collect your name, email, location or contacts.
Your choices (language, province, topics, saved stories) are stored <b>only on your device</b>. Uninstalling the app deletes them.</p>
<h2>Advertising</h2>
<p>The app shows ads from Google AdMob. Google may collect and use device identifiers (such as the advertising ID),
IP address and app interactions to show and measure ads. See <a href="https://policies.google.com/technologies/partner-sites">how Google uses information from apps that use its services</a>.
You can reset or delete your advertising ID in your Android settings.</p>
<h2>News and links</h2>
<p>Summaries are written with the help of AI from publicly available news, and each story names and links to its source.
When you open a full story, the publisher's website and its own privacy policy apply.</p>
<h2>Reporting a problem</h2>
<p>If you report a summary, your email app opens and you choose what to send. We use reports only to fix content.</p>
<h2>Children</h2><p>The app is not directed at children under 13.</p>
<h2>Contact</h2><p>Questions or requests: <a href="mailto:{{EMAIL}}">{{EMAIL}}</a></p>
<hr>
<h1>Politique de confidentialité</h1><p><i>Dernière mise à jour : 25 octobre 2026</i></p>
<p>Canada Shorts (« l'application ») présente de courts résumés de l'actualité canadienne avec des liens vers les éditeurs d'origine.</p>
<h2>Ce que nous recueillons</h2>
<p>Aucun compte n'est requis et nous ne recueillons ni votre nom, ni votre courriel, ni votre position, ni vos contacts.
Vos choix (langue, province, sujets, articles enregistrés) sont conservés <b>uniquement sur votre appareil</b>. Désinstaller l'application les supprime.</p>
<h2>Publicité</h2>
<p>L'application affiche des annonces de Google AdMob. Google peut recueillir et utiliser des identifiants de l'appareil (comme l'identifiant publicitaire),
l'adresse IP et les interactions avec l'application pour afficher et mesurer les annonces. Voir <a href="https://policies.google.com/technologies/partner-sites?hl=fr">comment Google utilise les données</a>.
Vous pouvez réinitialiser ou supprimer votre identifiant publicitaire dans les paramètres Android.</p>
<h2>Nouvelles et liens</h2>
<p>Les résumés sont rédigés avec l'aide de l'IA à partir de nouvelles publiques, et chaque nouvelle nomme sa source et y renvoie.
Lorsque vous ouvrez l'article complet, le site de l'éditeur et sa propre politique s'appliquent.</p>
<h2>Signaler un problème</h2>
<p>Si vous signalez un résumé, votre application de courriel s'ouvre et vous choisissez quoi envoyer. Les signalements servent uniquement à corriger le contenu.</p>
<h2>Enfants</h2><p>L'application ne s'adresse pas aux enfants de moins de 13 ans.</p>
<h2>Contact</h2><p>Questions ou demandes : <a href="mailto:{{EMAIL}}">{{EMAIL}}</a></p>
</body></html>"""


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
    (out / "privacy.html").write_text(PRIVACY_HTML.replace("{{EMAIL}}", config.CONTACT_EMAIL), encoding="utf-8")
    return counts


if __name__ == "__main__":
    print(export(sys.argv[1] if len(sys.argv) > 1 else "site"))
