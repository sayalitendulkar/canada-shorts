"""Settings, read from environment variables (see .env.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env_file(path: Path) -> None:
    """Read KEY=value lines from backend/.env (keeps secrets out of the code)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.split(" #")[0].strip().strip('"').strip("'"))


_load_env_file(BASE_DIR.parent / ".env")

DB_PATH = os.getenv("CS_DB_PATH", str(BASE_DIR.parent / "canada_shorts.db"))
SOURCES_FILE = os.getenv("CS_SOURCES_FILE", str(BASE_DIR / "sources.json"))

# AI summaries. Without a key the pipeline falls back to a trimmed feed excerpt.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SUMMARY_MODEL = os.getenv("CS_SUMMARY_MODEL", "claude-haiku-4-5")  # check current model names

# Google Gemini (free tier). Used first when a key is set. Leave the model empty to
# pick the newest free "Flash-Lite" (or "Flash") model automatically.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("CS_GEMINI_MODEL", "")

# Free tiers limit REQUESTS per day. Each request writes up to AI_BATCH_SIZE stories,
# most important first, only for stories from the last 24 hours. If Google says the
# daily limit is reached, the rest simply wait for the next day.
AI_DAILY_LIMIT = int(os.getenv("CS_AI_DAILY_REQUESTS", "150"))  # requests per day (both languages)
AI_BATCH_SIZE = int(os.getenv("CS_AI_BATCH_SIZE", "6"))
AI_MAX_REQUESTS_PER_RUN = int(os.getenv("CS_AI_REQUESTS_PER_RUN", "8"))
AI_FRENCH_SHARE = 0.4  # 40% of the daily AI quota is kept for French stories


def ai_limit(lang: str) -> int:
    fr = round(AI_DAILY_LIMIT * AI_FRENCH_SHARE)
    return fr if lang == "fr" else AI_DAILY_LIMIT - fr
AI_MAX_AGE_HOURS = 24
AI_PAUSE_SECONDS = float(os.getenv("CS_AI_PAUSE_SECONDS", "5"))

MAX_WORDS = 60
FETCH_TIMEOUT_S = 15
USER_AGENT = "CanadaShortsBot/0.1 (+https://example.com/bot; contact@example.com)"
CLUSTER_WINDOW_HOURS = 36
CLUSTER_THRESHOLD = 0.25  # TF-IDF cosine vs. the story centroid (tuned on real Oct 2026 feeds)

# Stories in clusters with at least this many outlets need an editor before publishing.
TOP_STORY_MIN_SOURCES = 3
OWNER_CAP_SHARE = 0.25  # max share of a feed page from one owner

ADMIN_TOKEN = os.getenv("CS_ADMIN_TOKEN", "change-me")

# Shown in the privacy policy and app (Google Play requires a real contact email).
CONTACT_EMAIL = os.getenv("CS_CONTACT_EMAIL", "your-email@example.com")

# 1 = big stories (3+ outlets) and flagged drafts wait for an editor at /admin.
# 0 = publish automatically (used online on GitHub, where nobody runs /admin);
#     flagged AI drafts still fall back to the publisher's own summary.
EDITOR_REVIEW = os.getenv("CS_EDITOR_REVIEW", "1") == "1"

# Skip feed items older than this (some government feeds return weeks of items).
MAX_ARTICLE_AGE_DAYS = 3

# Not news: ads, sponsored shopping posts, opinion columns. Matched against the
# article URL and the start of its headline (lower-case).
SKIP_URL_PARTS = ["/the-curator/", "/sponsored", "/partner-content", "/shopping/", "/commerce/", "/deals/",
                  "/opinion/", "/opinions/", "/chroniques/", "/chronique/", "/editorials/", "/editorial/",
                  "/lettres/", "/letters/", "/horoscope"]
SKIP_TITLE_STARTS = ["the curator:", "sponsored", "opinion:", "opinion |", "chronique |", "éditorial", "editorial:",
                     "letters:", "horoscope"]

# Bump when the grouping method changes: the next pipeline run regroups everything.
CLUSTER_VERSION = 2
