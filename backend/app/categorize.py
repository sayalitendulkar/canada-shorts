"""Rule-based category and province tagging (EN + FR). Good enough for an MVP;
replace with a small classifier once editors have labelled a few thousand stories."""
from .text import fold, keywords

CATEGORIES = [
    "top", "canada", "politics", "province", "business", "money", "canada_us", "world",
    "sports", "tech", "climate", "health", "indigenous", "entertainment",
]

LABELS = {
    "en": {
        "top": "Top Stories", "canada": "Canada", "politics": "Politics", "province": "My Province",
        "business": "Business", "money": "Cost of Living", "canada_us": "Canada–U.S.", "world": "World",
        "sports": "Sports", "tech": "Tech & Science", "climate": "Climate", "health": "Health",
        "indigenous": "Indigenous", "entertainment": "Culture",
    },
    "fr": {
        "top": "À la une", "canada": "Canada", "politics": "Politique", "province": "Ma province",
        "business": "Économie", "money": "Coût de la vie", "canada_us": "Canada–É.-U.", "world": "Monde",
        "sports": "Sports", "tech": "Techno et science", "climate": "Climat", "health": "Santé",
        "indigenous": "Autochtones", "entertainment": "Culture",
    },
}

# Keywords are accent-folded and lower-case.
RULES = {
    "canada_us": {"tariff", "tariffs", "cusma", "trump", "washington", "tarif", "tarifs", "aceum", "border", "frontiere"},
    "politics": {"parliament", "ottawa", "minister", "premier", "election", "liberal", "conservative", "ndp", "bloc",
                 "poilievre", "carney", "legislature", "parlement", "ministre", "election", "liberaux", "conservateurs",
                 "npd", "quebecois", "caq", "assemblee"},
    "money": {"rent", "groceries", "grocery", "mortgage", "inflation", "gas", "loyer", "epicerie", "hypotheque",
              "benefit", "benefits", "cpi", "affordability", "prix"},
    "business": {"tsx", "bank", "economy", "jobs", "unemployment", "earnings", "shares", "stocks", "rate", "rates",
                 "economie", "emplois", "chomage", "banque", "taux", "bourse"},
    "sports": {"nhl", "leafs", "canadiens", "oilers", "canucks", "flames", "jets", "senators", "raptors", "jays",
               "cfl", "grey", "mls", "whitecaps", "pwhl", "olympic", "olympics", "lnh", "hockey", "soccer", "goal",
               "playoffs", "series"},
    "tech": {"artificial", "intelligence", "artificielle", "tech", "technology", "startup", "software", "space", "science", "researchers", "ia",
             "technologie", "chercheurs", "spatiale"},
    "climate": {"wildfire", "wildfires", "climate", "flood", "flooding", "emissions", "carbon", "pipeline",
                "feux", "incendie", "incendies", "climat", "inondation", "inondations", "carbone"},
    "health": {"health", "hospital", "hospitals", "doctor", "doctors", "measles", "vaccine", "sante", "hopital",
               "hopitaux", "medecin", "medecins", "rougeole", "vaccin"},
    "indigenous": {"indigenous", "inuit", "metis", "autochtone", "autochtones", "reconciliation", "treaty"},
    "entertainment": {"film", "music", "festival", "concert", "album", "tiff", "netflix", "musique", "cinema"},
    "world": {"ukraine", "russia", "israel", "israelis", "gaza", "china", "india", "europe", "european", "nations-unies",
              "nato", "otan", "chine", "russie", "inde", "france", "italy", "germany", "iran", "japan", "mexico",
              "britain", "brazil", "turkey", "allemagne", "italie", "bresil", "turquie", "europeens"},
}

PROVINCES = {
    "ON": {"ontario", "toronto", "ottawa", "hamilton", "london", "mississauga", "brampton", "kitchener", "windsor"},
    "QC": {"quebec", "montreal", "laval", "gatineau", "sherbrooke", "saguenay"},
    "BC": {"columbia", "vancouver", "victoria", "surrey", "kelowna", "burnaby"},
    "AB": {"alberta", "calgary", "edmonton", "lethbridge"},
    "MB": {"manitoba", "winnipeg", "brandon"},
    "SK": {"saskatchewan", "regina", "saskatoon"},
    "NS": {"nova", "scotia", "halifax", "ecosse"},
    "NB": {"brunswick", "moncton", "fredericton", "brunswick"},
    "NL": {"newfoundland", "labrador", "terre-neuve"},
    "PE": {"pei", "charlottetown"},
    "YT": {"yukon", "whitehorse"},
    "NT": {"yellowknife", "northwest"},
    "NU": {"nunavut", "iqaluit"},
}


def categorize(title: str, excerpt: str, hint: str | None) -> str:
    title_kw, body_kw = keywords(title), keywords(excerpt)
    best, best_hits = None, 0
    for cat, words in RULES.items():
        hits = 2 * len(title_kw & words) + len(body_kw & words)  # title words count double
        if hits > best_hits:
            best, best_hits = cat, hits
    if best and best_hits >= 1:
        return best
    return hint if hint in CATEGORIES and hint != "top" else "canada"


def provinces(text: str) -> list[str]:
    kw = {fold(w) for w in keywords(text)}
    return sorted(code for code, words in PROVINCES.items() if kw & words)
