"""Google Gemini API (free tier) via plain HTTPS — no extra packages needed."""
import json
import logging
import re
import time

import httpx

from . import config

log = logging.getLogger(__name__)
BASE = "https://generativelanguage.googleapis.com/v1beta"


class QuotaExceeded(Exception):
    """The free daily/minute limit was hit; stop asking until later."""


def _headers() -> dict:
    return {"x-goog-api-key": config.GEMINI_API_KEY, "Content-Type": "application/json"}


def list_models() -> list[str]:
    r = httpx.get(f"{BASE}/models", params={"pageSize": 200}, headers=_headers(), timeout=20)
    r.raise_for_status()
    return [m["name"].removeprefix("models/") for m in r.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])]


def _version_key(name: str):
    nums = [int(n) for n in re.findall(r"\d+", name)]
    return nums or [0]


def candidates(names: list[str]) -> list[str]:
    """Free-tier-friendly order: newest stable Flash-Lite first, then newest Flash."""
    stable = [n for n in names if "gemini" in n and not re.search(r"preview|exp|tts|image|live|audio|thinking", n)]
    lite = sorted((n for n in stable if "flash-lite" in n), key=_version_key, reverse=True)
    flash = sorted((n for n in stable if "flash" in n and "lite" not in n), key=_version_key, reverse=True)
    return lite + flash


def pick_model(names: list[str]) -> str:
    c = candidates(names)
    if not c:
        raise RuntimeError("no Gemini Flash model available for this key")
    return c[0]


_queue: list[str] | None = None  # models still worth trying this run


def model() -> str:
    global _queue
    if config.GEMINI_MODEL:
        return config.GEMINI_MODEL
    if _queue is None:
        _queue = candidates(list_models())
        if not _queue:
            raise RuntimeError("no Gemini Flash model available for this key")
        log.info("using Gemini model %s", _queue[0])
    if not _queue:
        raise QuotaExceeded("no free Gemini model left today")
    return _queue[0]


def _drop_current_model(reason: str) -> None:
    if _queue and not config.GEMINI_MODEL:
        log.warning("Gemini model %s unavailable (%s); trying the next one", _queue.pop(0), reason[:120])


def _error_text(r: httpx.Response) -> str:
    try:
        return r.json().get("error", {}).get("message", r.text)[:400]
    except Exception:
        return r.text[:400]


def generate_json(prompt: str, _attempt: int = 0) -> dict:
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json", "maxOutputTokens": 600},
    }
    name = model()
    r = httpx.post(f"{BASE}/models/{name}:generateContent", headers=_headers(), json=body, timeout=60)
    if r.status_code in (404, 429) or (r.status_code == 400 and "not supported" in r.text.lower()):
        msg = _error_text(r)
        low = msg.lower()
        if _attempt < 4:
            if r.status_code == 429 and ("per minute" in low or "perminute" in low) and "per day" not in low:
                log.info("Gemini per-minute limit; waiting 60 s")
                time.sleep(60)
                return generate_json(prompt, _attempt + 1)
            if r.status_code == 404 or "limit: 0" in low or "per day" in low or "perday" in low:
                _drop_current_model(msg)  # this model has no (more) free quota: try the next
                if _queue:
                    return generate_json(prompt, _attempt + 1)
        if r.status_code == 429:
            raise QuotaExceeded(msg)
        raise RuntimeError(f"Gemini error {r.status_code}: {msg}")
    if r.status_code >= 400:
        raise RuntimeError(f"Gemini error {r.status_code}: {_error_text(r)}")
    parts = r.json()["candidates"][0]["content"]["parts"]
    text = "".join(p.get("text", "") for p in parts)
    return json.loads(text[text.find("{"): text.rfind("}") + 1])
