"""Text helpers: HTML stripping, tokenising (EN + FR), word limits."""
import html
import re
import unicodedata

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_WORD = re.compile(r"[\w'’-]+", re.UNICODE)

STOPWORDS = set(
    """a an the and or but if of to in on at by for with from as is are was were be been being it its
    this that these those he she they them his her their we our you your i not no yes will would can could
    should may might has have had do does did says said say after before over under into about than then
    there here what which who whom when where why how all any more most new up out also just
    le la les un une des du de d l et ou mais si à au aux en dans sur par pour avec sans est sont été être
    il elle ils elles son sa ses leur leurs nous vous je ne pas plus que qui quoi dont où ce cet cette ces
    selon a ont avait fait dit après avant entre comme aussi""".split()
)


def strip_html(raw: str | None) -> str:
    if not raw:
        return ""
    text = html.unescape(_TAG.sub(" ", raw))
    return _WS.sub(" ", text).strip()


def fold(word: str) -> str:
    """Lower-case and remove accents so 'Québec' == 'quebec'."""
    nfkd = unicodedata.normalize("NFKD", word.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def keywords(text: str) -> set[str]:
    out = set()
    for w in _WORD.findall(text):
        f = fold(w).strip("'’-")
        if len(f) > 2 and f not in STOPWORDS:
            out.add(f)
    return out


def word_count(text: str) -> int:
    return len(_WORD.findall(text))


def trim_words(text: str, limit: int) -> str:
    """Trim to <= limit words, ending on a sentence boundary when possible."""
    words = text.split()
    if len(words) <= limit:
        return text.strip()
    cut = " ".join(words[:limit])
    last_stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if last_stop > len(cut) * 0.5:
        return cut[: last_stop + 1]
    return cut.rstrip(",;:") + "…"


def numbers_in(text: str) -> set[str]:
    return set(re.findall(r"\d[\d,.]*", text.replace(" ", " ")))
