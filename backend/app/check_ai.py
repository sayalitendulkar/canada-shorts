"""Check that the AI key works:   python -m app.check_ai"""
import sys

from . import config


def main() -> int:
    if not config.GEMINI_API_KEY:
        print("No GEMINI_API_KEY found. Put it in the file backend\\.env  (see .env.example).")
        return 1
    from . import gemini
    try:
        names = gemini.list_models()
    except Exception as exc:
        print("Could not talk to Gemini with this key:", str(exc)[:300])
        print("Check that the key was copied fully from aistudio.google.com (Get API key).")
        return 1
    order = [config.GEMINI_MODEL] if config.GEMINI_MODEL else gemini.candidates(names)
    print(f"Key works. {len(names)} models available. Will try, in order: {', '.join(order[:4])}")
    sample = ("The Bank of Canada held its key interest rate at 2.25 per cent on Wednesday. Governor Tiff Macklem said "
              "inflation is close to the 2 per cent target but trade uncertainty with the United States is weighing on "
              "business investment. Economists had expected the hold. The next rate decision is in December.")
    try:
        data = gemini.generate_json(
            "Summarise in at most 40 words as JSON {\"headline\": \"...\", \"summary\": \"...\"}:\n" + sample)
    except gemini.QuotaExceeded as exc:
        print("Key works, but Google refused because of a usage limit. Google says:")
        print("   ", exc)
        return 0
    except Exception as exc:
        print("The test summary failed:", exc)
        return 1
    print("Model used:", gemini.model())
    print("Test headline:", data.get("headline"))
    print("Test summary: ", data.get("summary"))
    print("All good. Run:  python -m app.pipeline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
