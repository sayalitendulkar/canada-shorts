"""Read the public text of an article so the AI can write an accurate summary.

Rules: only publicly reachable pages (never paywalled sources), follow each
site's robots.txt, keep the text only in memory while summarising (it is never
stored or shown in the app)."""
import logging
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from . import config

log = logging.getLogger(__name__)
_robots: dict[str, RobotFileParser | None] = {}

SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "figure", "figcaption", "button"}


class _Paragraphs(HTMLParser):
    """Collect the text of <p> elements, preferring those inside <article>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.in_article = 0
        self.in_p = 0
        self.buf: list[str] = []
        self.article_ps: list[str] = []
        self.other_ps: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip += 1
        elif tag == "article":
            self.in_article += 1
        elif tag == "p" and not self.skip:
            self.in_p += 1
            self.buf = []

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        elif tag == "article" and self.in_article:
            self.in_article -= 1
        elif tag == "p" and self.in_p:
            self.in_p -= 1
            text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
            if len(text) >= 60:  # skip captions, bylines, buttons
                (self.article_ps if self.in_article else self.other_ps).append(text)

    def handle_data(self, data):
        if self.in_p and not self.skip:
            self.buf.append(data)


def extract_text(html: str, max_words: int = 900) -> str:
    p = _Paragraphs()
    p.feed(html)
    paras = p.article_ps if len(" ".join(p.article_ps)) > 400 else p.article_ps + p.other_ps
    words = " ".join(paras).split()
    return " ".join(words[:max_words])


def _allowed(client: httpx.Client, url: str) -> bool:
    parts = urlsplit(url)
    root = f"{parts.scheme}://{parts.netloc}"
    if root not in _robots:
        rp = RobotFileParser()
        try:
            r = client.get(root + "/robots.txt")
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
            _robots[root] = rp
        except Exception:
            _robots[root] = None  # robots.txt unreachable: be safe, don't fetch
    rp = _robots[root]
    return bool(rp and rp.can_fetch(config.USER_AGENT, url))


def fetch_article_text(url: str, client: httpx.Client | None = None) -> str:
    """Return up to ~900 words of article text, or '' if not allowed/available."""
    own = client is None
    client = client or httpx.Client(timeout=config.FETCH_TIMEOUT_S, follow_redirects=True,
                                    headers={"User-Agent": config.USER_AGENT})
    try:
        if not _allowed(client, url):
            return ""
        r = client.get(url)
        if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
            return ""
        return extract_text(r.text)
    except Exception as exc:
        log.info("could not read %s: %s", url, exc)
        return ""
    finally:
        if own:
            client.close()
