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
1. "headline": a plain, factual headline of at most 12 words. No clickbait, no questions.
2. "summary": between 50 and {max_words} words, so a reader understands the whole story without opening the article:
   who, what, where, when, key numbers, and why it matters to Canadians.
Rules: facts only; attribute claims and opinions to who made them ("Ottawa says", "critics argue");
no adjectives that take a side; no information that is not in the source text; Canadian spelling.
Return JSON only: {{"headline": "...", "summary": "..."}}

Sources:
{sources}""",
    "fr": """Tu rédiges des résumés pour une application de nouvelles canadienne. En utilisant SEULEMENT le texte source ci-dessous, écris en français standard, dans tes propres mots (ne copie jamais de phrases) :
1. "headline" : un titre factuel d'au plus 12 mots. Pas de piège à clics, pas de question.
2. "summary" : entre 50 et {max_words} mots, pour que le lecteur comprenne toute la nouvelle sans ouvrir l'article :
   qui, quoi, où, quand, les chiffres clés, et pourquoi c'est important pour les Canadiens.
Règles : faits seulement; attribue les affirmations et opinions à leur auteur (« Ottawa affirme », « selon les critiques »);
aucun adjectif partisan; aucune information absente du texte source.
Réponds seulement en JSON : {{"headline": "...", "summary": "..."}}

Sources :
{sources}""",
}


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
    """No AI: use the lead article's own headline and trimmed excerpt."""
    lead = articles[0]
    body = lead["excerpt"] or lead["title"]
    return lead["title"], trim_words(body, config.MAX_WORDS)


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
