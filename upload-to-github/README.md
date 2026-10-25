# Canada Shorts — starter code

Canadian news in 60 words, English and French. Two parts:

```
backend/   Python: RSS ingest → story clustering → AI summary + checks → editor review → FastAPI
app/       Flutter (Android first): onboarding, swipe feed, categories, bias bar, bookmarks, settings
```

## 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY for AI summaries (optional)
export $(grep -v '^#' .env | xargs)                    # or use your own env loader

pytest -q                   # 5 offline tests
python -m app.pipeline      # fetch feeds once and build stories
uvicorn app.api:app --reload
```

- API docs: http://localhost:8000/docs
- Editor console: http://localhost:8000/admin (enter `CS_ADMIN_TOKEN`)
- Feed: `GET /feed?lang=en&category=top&province=ON`
- Run the pipeline every 10 minutes (cron: `*/10 * * * * cd /srv && python -m app.pipeline`).

**How a story flows:** feeds in `app/sources.json` → articles stored → similar articles grouped into one
story (same language, 36-hour window) → AI writes a ≤60-word headline + summary from feed text only →
automatic checks (word count, loaded words, every number must appear in the sources) → stories covered
by 3+ outlets, or failing a check, wait in the editor queue; others publish. Without an API key the
card uses the lead publisher's own excerpt, trimmed to 60 words.

**Before launch:** test every feed URL in `sources.json` (some were not verifiable from the build
sandbox), read each publisher's feed terms (La Presse requires its logo), and move from SQLite to
PostgreSQL in a Canadian cloud region.

## 2. Flutter app

Needs Flutter 3.22+.

```bash
cd app
flutter create . --platforms=android --org ca.canadashorts --project-name canada_shorts
flutter pub get
flutter run                                   # emulator talks to http://10.0.2.2:8000
flutter run --dart-define=API_BASE=https://api.yourdomain.ca   # real server
```

`flutter create .` generates the Android folder without touching `lib/`. Then edit
`android/app/src/main/AndroidManifest.xml`:

```xml
<manifest ...>
    <uses-permission android:name="android.permission.INTERNET"/>
    <queries>
        <intent>
            <action android:name="android.intent.action.VIEW"/>
            <data android:scheme="https"/>
        </intent>
    </queries>
    <application ...>
```

For local testing over plain http also add `android:usesCleartextTraffic="true"` to `<application>`
(remove it for release).

Set your real contact email and privacy URL in `lib/config.dart` — Google Play's news policy requires an
in-app contact.

## What's next (v2)

Push notifications (Firebase Cloud Messaging), personalised ranking, NHL scores, Environment Canada
alerts, cross-language clustering with embeddings, publisher-logo display, and a web page per card.

## 3. Online, free (GitHub)

`.github/workflows/news.yml` runs the news program every 30 minutes on GitHub and
publishes the result as a website: `https://<username>.github.io/<repo>/`.

- Add your Gemini key in the repo: Settings → Secrets and variables → Actions → New
  repository secret, name `GEMINI_API_KEY`.
- Settings → Pages → Source: **GitHub Actions**.
- Online, stories publish automatically (`CS_EDITOR_REVIEW=0`); AI drafts that fail the
  checks show the publisher's own summary instead.
- The phone app can read the same files: `data/feed_en.json`, `data/feed_fr.json`.

On Windows, the commands in section 1 are the same except: `py -3.13 -m venv .venv`,
`.venv\Scripts\activate`, and put settings in `backend\.env` instead of `export`.
