"""Configuration for multilingual CTA extraction."""

from pathlib import Path

# File paths
BASE_DIR = Path(__file__).resolve().parent
URL_SOURCE_FILE = BASE_DIR / "product_urls.json"
OUTPUT_FILE = BASE_DIR / "cta_features.json"

# Browser settings
HEADLESS = True
PAGE_TIMEOUT_MS = 45_000
NETWORK_IDLE_TIMEOUT_MS = 10_000
VIEWPORT = {"width": 1440, "height": 900}
SCROLL_PAUSE_MS = 350
MAX_SCROLL_STEPS = 20
CTA_SELECTOR = (
    "a[href], button, input[type='button'], input[type='submit'], [role='button']"
)

# Text that must never be treated as a CTA.
EXCLUDE_TEXT = (
    "cookie",
    "cookies",
    "accept all",
    "reject all",
    "essential cookies",
    "cookie settings",
    "manage cookies",
    "j’accepte tous les cookies",
    "j'accepte tous les cookies",
    "accepter les cookies",
    "refuser les cookies",
    "cookies essentiels",
    "paramètres des cookies",
    "aanvaard alle cookies",
    "accepteer alle cookies",
    "alle cookies aanvaarden",
    "alle cookies accepteren",
    "cookie-instellingen",
    "cookievoorkeuren",
    "home",
    "menu",
    "navigation",
    "login",
    "log in",
    "sign in",
    "connexion",
    "se connecter",
    "inloggen",
    "aanmelden",
    "search",
    "recherche",
    "zoeken",
    "privacy",
    "privacy policy",
    "legal",
    "juridique",
    "disclaimer",
    "sitemap",
    "plan du site",
    "skip to main content",
    "skip to content",
    "powered by onetrust",
    "onetrust",
    "opens in a new tab",
    "opent in een nieuw tabblad",
    "ouvre dans un nouvel onglet",
)

# CTA intent labels and their English, French, and Dutch phrases
CTA_TYPE_KEYWORDS = {
    "Apply": (
        "apply now",
        "apply",
        "request",
        "demandez",
        "demander",
        "souscrivez",
        "souscrire",
        "vraag aan",
        "aanvragen",
        "aanvraag",
    ),
    "Buy": (
        "buy now",
        "buy",
        "purchase",
        "achetez",
        "acheter",
        "koop",
        "kopen",
    ),
    "Open": (
        "open an account",
        "open account",
        "open",
        "ouvrez",
        "ouvrir",
        "open een rekening",
        "openen",
    ),
    "Learn": (
        "learn more",
        "find out more",
        "read more",
        "more information",
        "more info",
        "discover",
        "en savoir plus",
        "plus d'informations",
        "plus d'infos",
        "découvrir",
        "decouvrir",
        "meer informatie",
        "meer info",
        "meer weten",
        "lees meer",
        "ontdekken",
        "ontdek",
    ),
    "Contact": (
        "contact us",
        "make an appointment",
        "book an appointment",
        "appointment",
        "contact",
        "contactez-nous",
        "contactez",
        "prendre rendez-vous",
        "rendez-vous",
        "contacteer ons",
        "contacteer",
        "maak een afspraak",
        "afspraak",
    ),
    "Calculate": (
        "calculate your premium",
        "calculate",
        "calculator",
        "work out",
        "get a quote",
        "quote",
        "simulate",
        "calculez",
        "calculer",
        "simulez",
        "simuler",
        "obtenir un devis",
        "devis",
        "bereken",
        "berekenen",
        "simuleer",
        "simuleren",
        "offerte",
    ),
}
CTA_KEYWORDS = tuple(
    sorted(
        {word for words in CTA_TYPE_KEYWORDS.values() for word in words},
        key=len,
        reverse=True,
    )
)
CTA_CLASS_MARKERS = (
    "cta",
    "btn-primary",
    "button-primary",
    "primary-button",
    "primary_button",
    "action-button",
    "action_button",
)

# Optional diagnostics
DEBUG_DETECTED_CTAS = False
