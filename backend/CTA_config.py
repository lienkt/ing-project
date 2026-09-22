"""
Configuration for multilingual CTA feature extraction.

Supported languages:
- English
- French
- Dutch
"""

from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

URL_SOURCE_FILE = BASE_DIR / "product_urls.json"
OUTPUT_FILE = BASE_DIR / "cta_features.json"


# ============================================================
# PLAYWRIGHT SETTINGS
# ============================================================

HEADLESS = True

PAGE_TIMEOUT_MS = 45_000
NETWORK_IDLE_TIMEOUT_MS = 10_000

VIEWPORT = {
    "width": 1440,
    "height": 900,
}

SCROLL_PAUSE_MS = 350
MAX_SCROLL_STEPS = 20


# ============================================================
# CTA ELEMENT SELECTOR
# ============================================================

CTA_SELECTOR = (
    "a[href], "
    "button, "
    "input[type='button'], "
    "input[type='submit'], "
    "[role='button']"
)


# ============================================================
# TEXT THAT SHOULD NEVER BE TREATED AS A CTA
# ============================================================

EXCLUDE_TEXT = [

    # --------------------------------------------------------
    # Cookies / Privacy / Legal
    # --------------------------------------------------------

    "cookie",
    "cookies",
    "accept all",
    "accept all cookies",
    "reject all",
    "reject all cookies",
    "essential cookies",
    "essential cookies only",
    "cookie settings",
    "cookie preferences",
    "manage cookies",

    # French
    "j’accepte tous les cookies",
    "j'accepte tous les cookies",
    "accepter tous les cookies",
    "accepter les cookies",
    "refuser les cookies",
    "cookies essentiels",
    "paramètres des cookies",
    "parametres des cookies",

    # Dutch
    "aanvaard alle cookies",
    "accepteer alle cookies",
    "alle cookies aanvaarden",
    "alle cookies accepteren",
    "essentiële cookies",
    "essentiele cookies",
    "cookie-instellingen",
    "cookievoorkeuren",

    "privacy",
    "privacy policy",
    "privacybeleid",
    "legal",
    "juridique",
    "wettelijk",
    "disclaimer",
    "sitemap",
    "plan du site",
    "sitemap",

    # --------------------------------------------------------
    # Technical / navigation
    # --------------------------------------------------------

    "skip to main content",
    "skip to content",

    "powered by onetrust",
    "onetrust",

    "opens in a new tab",
    "opent in een nieuw tabblad",
    "ouvre dans un nouvel onglet",

    "questions & contact",
    "questions and contact",
    "questions et contact",

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
]


# ============================================================
# CTA TYPE KEYWORDS
# ============================================================

CTA_TYPE_KEYWORDS = {

    # --------------------------------------------------------
    # Calculate / Quote / Simulation
    # --------------------------------------------------------

    "Calculate": [
        # English
        "calculate your premium",
        "calculate your price",
        "calculate your insurance",
        "calculate",
        "calculator",
        "work out",
        "work out your insurance",
        "work out your price",
        "get a quote",
        "get your quote",
        "quote",
        "simulate",
        "simulation",

        # French
        "calculez votre prime",
        "calculez votre prix",
        "calculer votre prix",
        "calculer",
        "calculez",
        "calcul",
        "simulatez",
        "simuler",
        "simulation",
        "obtenir un devis",
        "demander un devis",
        "devis",

        # Dutch
        "bereken uw premie",
        "bereken uw prijs",
        "bereken je prijs",
        "bereken uw verzekering",
        "bereken",
        "berekenen",
        "bereken uw",
        "simuleer uw verzekering",
        "simuleer",
        "simuleren",
        "simulatie",
        "offerte",
        "offerte aanvragen",
    ],

    # --------------------------------------------------------
    # Apply / Request
    # --------------------------------------------------------

    "Apply": [
        # English
        "apply now",
        "apply online",
        "apply",
        "request",
        "request now",
        "request a quote",
        "request information",
        "start application",
        "get started",

        # French
        "demandez",
        "demander",
        "demandez maintenant",
        "souscrivez",
        "souscrire",
        "souscrivez maintenant",
        "faire une demande",
        "introduire une demande",

        # Dutch
        "vraag aan",
        "aanvragen",
        "aanvraag",
        "vraag nu aan",
        "online aanvragen",
        "aanvragen",
        "start aanvraag",
    ],

    # --------------------------------------------------------
    # Buy
    # --------------------------------------------------------

    "Buy": [
        # English
        "buy now",
        "buy",
        "purchase",
        "purchase now",
        "order now",

        # French
        "achetez",
        "acheter",
        "acheter maintenant",
        "commander",
        "commandez",

        # Dutch
        "koop",
        "kopen",
        "koop nu",
        "bestellen",
        "bestel",
    ],

    # --------------------------------------------------------
    # Open
    # --------------------------------------------------------

    "Open": [
        # English
        "open an account",
        "open account",
        "open a bank account",
        "open your account",
        "open now",

        # French
        "ouvrez un compte",
        "ouvrir un compte",
        "ouvrez votre compte",
        "ouvrir votre compte",

        # Dutch
        "open een rekening",
        "rekening openen",
        "open rekening",
        "open uw rekening",
        "rekening openen",
    ],

    # --------------------------------------------------------
    # Learn
    # --------------------------------------------------------

    "Learn": [
        # English
        "learn more",
        "find out more",
        "read more",
        "more information",
        "more info",
        "discover",
        "discover more",
        "find out",
        "learn more about",
        "view details",
        "see details",

        # French
        "en savoir plus",
        "plus d'informations",
        "plus d'infos",
        "découvrir",
        "decouvrir",
        "découvrez",
        "decouvrez",
        "voir plus",
        "lire plus",
        "lire davantage",
        "plus de détails",
        "voir les détails",

        # Dutch
        "meer informatie",
        "meer info",
        "meer weten",
        "lees meer",
        "ontdekken",
        "ontdek",
        "ontdek meer",
        "bekijk meer",
        "meer details",
        "bekijk de details",
    ],

    # --------------------------------------------------------
    # Contact
    # --------------------------------------------------------

    "Contact": [
        # English
        "contact us",
        "contact",
        "make an appointment",
        "book an appointment",
        "appointment",
        "schedule an appointment",
        "talk to us",
        "speak to us",

        # French
        "contactez-nous",
        "contactez",
        "nous contacter",
        "prendre rendez-vous",
        "rendez-vous",
        "prendre un rendez-vous",
        "parler à un conseiller",

        # Dutch
        "contacteer ons",
        "contacteer",
        "contact",
        "maak een afspraak",
        "afspraak",
        "een afspraak maken",
        "plan een afspraak",
    ],

    # --------------------------------------------------------
    # Compare
    # --------------------------------------------------------

    "Compare": [
        # English
        "compare",
        "compare products",
        "compare accounts",
        "compare insurance",
        "compare prices",
        "compare options",
        "compare offers",
        "compare savings accounts",

        # French
        "comparer",
        "comparez",
        "comparer les produits",
        "comparer les comptes",
        "comparer les assurances",
        "comparer les offres",

        # Dutch
        "vergelijk",
        "vergelijken",
        "vergelijk producten",
        "vergelijk rekeningen",
        "vergelijk verzekeringen",
        "vergelijk opties",
        "vergelijk aanbiedingen",
        "spaarrekeningen vergelijken",
    ],
}


# ============================================================
# ALL CTA KEYWORDS
# ============================================================

CTA_KEYWORDS = sorted(
    {
        keyword
        for keywords in CTA_TYPE_KEYWORDS.values()
        for keyword in keywords
    },
    key=len,
    reverse=True,
)


# ============================================================
# CSS CLASS MARKERS
# ============================================================

CTA_CLASS_MARKERS = (
    "cta",
    "btn-primary",
    "button-primary",
    "primary-button",
    "primary_button",
    "action-button",
    "action_button",
    "call-to-action",
    "call_to_action",
    "main-cta",
    "main_cta",
)


# ============================================================
# OPTIONAL DEBUG OUTPUT
# ============================================================

# False = preserve the clean production output.
# True = include all detected CTA candidates.
DEBUG_DETECTED_CTAS = False