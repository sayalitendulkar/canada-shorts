"""Write the 60-word card summary for a story.

The AI only sees the feed text (headlines + excerpts) from the outlets in the
cluster, never full paywalled articles. Every draft goes through automatic
checks; anything that fails falls back to a trimmed excerpt and is sent to
editor review."""
import json
import logging
import re

from . import config
from .text import numbers_in, trim_words, word_count

log = logging.getLogger(__name__)

# Loaded words we never want in our own voice. Quoting a source is fine
# (the check ignores text inside quotation marks).
LOADED_WORDS = {
    "en": ["slams", "blasts", "destroys", "shocking", "radical", "extremist", "disastrous", "heroic",
           "outrageous", "woke", "far-left", "far-right", "regime", "chaos"],
    "fr": ["fustige", "pulvérise", "choquant", "radical", "extrémiste", "désastreux", "héroïque",
           "scandaleux", "woke", "extrême gauche", "extrême droite", "régime", "chaos"],
}

PROMPT = {
    "en": """You write news summaries for a Canadian news app. Using ONLY the source text below, write in your own words (never copy sentences):
1. "headline": a clear, specific headline of 8 to 12 words in present tense that says who did what (like Inshorts). No clickbait, no questions, no outlet names, no "live updates".
2. "summary": between 50 and {max_words} words, so a reader understands the whole story without opening the article:
   who, what, where, when, key numbers, and why it matters to Canadians.
Rules: facts only; attribute claims and opinions to who made them ("Ottawa says", "critics argue");
no adjectives that take a side; no information that is not in the source text;
Canadian Press style: Canadian spelling (centre, colour, defence, criticize), "per cent" not "percent".
Return JSON only: {{"headline": "...", "summary": "..."}}

Sources:
{sources}""",
    "fr": """Tu rédiges des résumés pour une application de nouvelles canadienne. En utilisant SEULEMENT le texte source ci-dessous, écris en français standard, dans tes propres mots (ne copie jamais de phrases) :
1. "headline" : un titre clair et précis de 8 à 12 mots, au présent, qui dit qui fait quoi. Pas de piège à clics, pas de question, pas de nom de média, pas de « en direct ».
2. "summary" : entre 50 et {max_words} mots, pour que le lecteur comprenne toute la nouvelle sans ouvrir l'article :
   qui, quoi, où, quand, les chiffres clés, et pourquoi c'est important pour les Canadiens.
Règles : faits seulement; attribue les affirmations et opinions à leur auteur (« Ottawa affirme », « selon les critiques »);
aucun adjectif partisan; aucune information absente du texte source; style de La Presse canadienne (« 2,25 % »).
Réponds seulement en JSON : {{"headline": "...", "summary": "..."}}

Sources :
{sources}""",
}


BATCH_PROMPT = {
    "en": """You write news cards for a Canadian news app, like Inshorts. For EACH story below, using ONLY that story's source text, write in your own words (never copy sentences):
- "headline": a clear, specific headline of 8 to 12 words in present tense that says who did what. No clickbait, no questions, no outlet names, no "live updates".
- "summary": {min_words} to {max_words} words so a reader understands the whole story without opening the article: who, what, where, when, key numbers, why it matters to Canadians. If the source is short, write less rather than adding anything.
Rules: facts only; attribute claims and opinions ("Ottawa says", "critics argue"); no adjectives that take a side; no information that is not in that story's source text; never mix stories;
Canadian Press style: Canadian spelling (centre, colour, defence, criticize), "per cent" not "percent".
Return JSON only: {{"stories": [{{"id": <story number>, "headline": "...", "summary": "..."}}, ...]}} with one entry per story.

{stories}""",
    "fr": """Tu rédiges des fiches de nouvelles pour une application canadienne, comme Inshorts. Pour CHAQUE nouvelle ci-dessous, en utilisant SEULEMENT son texte source, écris en français standard, dans tes propres mots (ne copie jamais de phrases) :
- "headline" : un titre clair et précis de 8 à 12 mots, au présent, qui dit qui fait quoi. Pas de piège à clics, pas de question, pas de nom de média, pas de « en direct ».
- "summary" : de {min_words} à {max_words} mots pour que le lecteur comprenne toute la nouvelle sans ouvrir l'article : qui, quoi, où, quand, chiffres clés, pourquoi c'est important pour les Canadiens. Si la source est courte, écris moins plutôt que d'ajouter quoi que ce soit.
Règles : faits seulement; attribue les affirmations et opinions; aucun adjectif partisan; aucune information absente du texte source de cette nouvelle; ne mélange jamais les nouvelles;
style de La Presse canadienne (« 2,25 % »).
Réponds seulement en JSON : {{"stories": [{{"id": <numéro>, "headline": "...", "summary": "..."}}, ...]}} avec une entrée par nouvelle.

{stories}""",
}

# Bits that outlets put in titles but that don't belong in a clean headline.
_TITLE_JUNK = [
    r"\s*[|\-–—]\s*(CBC News|CTV News|Global News|The Globe and Mail|National Post|Radio-Canada|La Presse|Le Devoir|The Narwhal)\s*$",
    r"\s*(Live updates here|Live updates|LIVE UPDATES|En direct|EN DIRECT)\.?\s*$",
    r"^\s*(LIVE|VIDEO|WATCH|PHOTOS|BREAKING|UPDATE|EN DIRECT|VIDÉO|EN IMAGES)\s*[:|\-–]\s*",
]


def clean_title(title: str) -> str:
    t = " ".join((title or "").split())
    for _ in range(2):
        for pat in _TITLE_JUNK:
            t = re.sub(pat, "", t, flags=re.IGNORECASE)
    return t.strip(" .")


def build_source_block(articles, full_text: str = "") -> str:
    lines = []
    for a in articles[:6]:
        lines.append(f"- [{a['source_name']}] {a['title']}. {a['excerpt'][:600]}")
    if full_text:
        lines.append("\nArticle text:\n" + full_text)
    return "\n".join(lines)


def check_summary(summary: str, headline: str, articles, lang: str, full_text: str = "") -> list[str]:
    """Return a list of problems; empty means OK to publish."""
    problems = []
    if not summary or not headline:
        problems.append("empty")
        return problems
    if word_count(summary) > config.MAX_WORDS:
        problems.append(f"too_long:{word_count(summary)}")
    unquoted = re.sub(r"[\"“«][^\"”»]*[\"”»]", " ", f"{headline} {summary}").lower()
    for w in LOADED_WORDS.get(lang, []):
        if re.search(rf"\b{re.escape(w)}\b", unquoted):
            problems.append(f"loaded_word:{w}")
    source_text = " ".join(f"{a['title']} {a['excerpt']}" for a in articles) + " " + full_text
    src_nums = {n.strip(".,") for n in numbers_in(source_text)}
    for n in numbers_in(f"{headline} {summary}"):
        if n.strip(".,") not in src_nums:
            problems.append(f"unsupported_number:{n}")
    return problems


def fallback(articles) -> tuple[str, str]:
    """No AI: use the lead article's own (cleaned) headline and the longest excerpt."""
    lead = articles[0]
    headline = clean_title(lead["title"]) or lead["title"]
    excerpts = [a["excerpt"] for a in articles if a["excerpt"] and a["excerpt"].strip() != a["title"].strip()]
    body = max(excerpts, key=lambda e: len(e.split())) if excerpts else lead["title"]
    return headline, trim_words(body, config.MAX_WORDS)


def ai_summary(articles, lang: str, full_text: str = "") -> tuple[str, str] | None:
    """Ask Gemini (free tier) or Claude for a draft. Raises gemini.QuotaExceeded
    when the free limit is hit so the pipeline can stop asking for today."""
    prompt = PROMPT[lang].format(max_words=config.MAX_WORDS, sources=build_source_block(articles, full_text))
    if config.GEMINI_API_KEY:
        from . import gemini
        try:
            data = gemini.generate_json(prompt)
            return data["headline"].strip(), data["summary"].strip()
        except gemini.QuotaExceeded:
            raise
        except Exception as exc:
            log.warning("Gemini summary failed: %s", exc)
            return None
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            msg = client.messages.create(model=config.SUMMARY_MODEL, max_tokens=400,
                                         messages=[{"role": "user", "content": prompt}])
            text = msg.content[0].text
            data = json.loads(text[text.find("{"): text.rfind("}") + 1])
            return data["headline"].strip(), data["summary"].strip()
        except Exception as exc:
            log.warning("AI summary failed: %s", exc)
    return None


def ai_batch(items, lang: str) -> dict:
    """Several stories in ONE request (free tiers limit requests per day, not stories).
    items: list of (key, articles, full_text). Returns {key: (headline, summary)}.
    Raises gemini.QuotaExceeded when the free limit is hit."""
    blocks = []
    for i, (_, arts, full) in enumerate(items, 1):
        blocks.append(f"=== Story {i} ===\n" + build_source_block(arts, full[:2500]))
    prompt = BATCH_PROMPT[lang].format(min_words=40, max_words=config.MAX_WORDS, stories="\n\n".join(blocks))
    if not config.GEMINI_API_KEY:
        return {}
    from . import gemini
    try:
        data = gemini.generate_json(prompt, max_tokens=300 * len(items) + 200)
    except gemini.QuotaExceeded:
        raise
    except Exception as exc:
        log.warning("Gemini batch failed: %s", exc)
        return {}
    out = {}
    for entry in (data.get("stories") or []) if isinstance(data, dict) else []:
        try:
            idx = int(entry["id"]) - 1
            if 0 <= idx < len(items) and entry.get("headline") and entry.get("summary"):
                out[items[idx][0]] = (str(entry["headline"]).strip(), str(entry["summary"]).strip())
        except (KeyError, TypeError, ValueError):
            continue
    return out


def summarize_batch(items, lang: str) -> dict:
    """Like summarize() for several stories at once. Returns {key: result dict}."""
    drafts = ai_batch(items, lang)
    results = {}
    for key, arts, full in items:
        draft = drafts.get(key)
        if draft:
            headline, summary = draft
            problems = check_summary(summary, headline, arts, lang, full)
            if not problems:
                results[key] = {"headline": headline, "summary": summary, "summary_by": "ai", "problems": []}
                continue
            log.info("AI draft rejected by checks: %s", problems)
        headline, summary = fallback(arts)
        results[key] = {"headline": headline, "summary": summary, "summary_by": "excerpt",
                        "problems": [] if draft is None else ["ai_draft_failed_checks"]}
    return results


def ai_enabled() -> bool:
    return bool(config.GEMINI_API_KEY or config.ANTHROPIC_API_KEY)


def summarize(articles, lang: str, full_text: str = "", use_ai: bool = True) -> dict:
    """Returns {headline, summary, summary_by, problems}."""
    result = ai_summary(articles, lang, full_text) if use_ai else None
    if result:
        headline, summary = result
        problems = check_summary(summary, headline, articles, lang, full_text)
        if not problems:
            return {"headline": headline, "summary": summary, "summary_by": "ai", "problems": []}
        log.info("AI draft rejected by checks: %s", problems)
    headline, summary = fallback(articles)
    return {"headline": headline, "summary": summary, "summary_by": "excerpt",
            "problems": [] if result is None else ["ai_draft_failed_checks"]}
