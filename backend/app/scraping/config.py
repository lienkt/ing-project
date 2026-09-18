"""Supported scraping cases — edit this list when adding a finished scraper.

1. Implement the function in functions.py or a bank-specific file.
2. Test it.
3. Import it here and add its exact normalized case below.
Unregistered cases require manual scraping. Never register unfinished functions.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field

from app.schemas.automation import build_case_key
from app.scraping.functions import scrape_demo_page, scrape_ing_youth_account_en

# Explicit cases only. Unregistered combinations require manual collection.
# Each real product/language gets its own named function, even within one bank.
SCRAPING_SUPPORT = {
    # ING — real product cases
    build_case_key(
        "ING", "Current Account", "ING Youth Account", "EN"
    ): scrape_ing_youth_account_en,
    # Synthetic demo cases only — shared fabricated content, no website selectors.
    build_case_key(
        "ING", "Current Account", "ING example current account", "EN"
    ): scrape_demo_page,
    build_case_key(
        "KBC", "Current Account", "KBC example current account", "EN"
    ): scrape_demo_page,
}


# Shared browser settings and optional standalone scoring vocabulary.
COLLECTION_TIMEOUT_SECONDS = 120
LANGUAGE_LOCALES = {
    "English": ("en", "en-BE"),
    "Dutch": ("nl", "nl-BE"),
    "French": ("fr", "fr-BE"),
}

DEFAULT_FINANCIAL_TERMS_NL = (
    "rente",
    "rentevoet",
    "interest",
    "interestvoet",
    "basisrente",
    "getrouwheidspremie",
    "spaarrekening",
    "spaarrekeningen",
    "belasting",
    "belastingen",
    "roerende voorheffing",
    "deposito",
    "depositobescherming",
    "garantiefonds",
    "voorwaarden",
    "voorwaarde",
    "kosten",
    "risico",
    "fiscale",
    "fiscaliteit",
    "minimum",
    "maximum",
    "vergoeding",
    "premie",
    "waarborg",
    "aansprakelijkheid",
    "uitsluiting",
    "vrijstelling",
    "schadevergoeding",
    "kredietopening",
)

DEFAULT_FINANCIAL_TERMS_EN = (
    "interest",
    "interest rate",
    "savings account",
    "fee",
    "fees",
    "conditions",
    "terms",
    "deposit",
    "deposit protection",
    "guarantee scheme",
    "minimum",
    "maximum",
    "tax",
    "withholding tax",
    "risk",
    "reward",
    "loan",
    "repayment",
    "apr",
    "premium",
    "insurance",
    "cover",
    "excess",
)


NOISE_SELECTORS = (
    "script",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "header",
    "footer",
    "nav",
    '[class*="cookie"]',
    '[id*="cookie"]',
    '[class*="consent"]',
    '[id*="consent"]',
    '[class*="chatbot"]',
    '[class*="chat-bot"]',
    '[id*="chatbot"]',
    '[id*="chat-bot"]',
    '[class*="search-overlay"]',
    '[class*="modal"]',
    '[class*="overlay"]',
)


@dataclass
class SiteConfig:
    """Everything that is allowed to differ between banks."""

    bank: str
    product: str
    url: str
    language: str = "nl"  # "nl" or "en" -> default vocabulary
    financial_terms: Iterable[str] | None = None
    heading_exclude: Iterable[str] = field(default_factory=tuple)
    paragraph_exclude: Iterable[str] = field(default_factory=tuple)
    bullet_exclude: Iterable[str] = field(default_factory=tuple)
    clean_page: bool = True
    main_selector: str | None = None
    ready_selector: str | None = None
    wait_ms: int = 3000
    viewport: dict = field(default_factory=lambda: {"width": 1440, "height": 1000})
    locale: str = "nl-BE"

    def terms(self) -> Iterable[str]:
        if self.financial_terms is not None:
            return self.financial_terms
        vocabularies = {
            "en": DEFAULT_FINANCIAL_TERMS_EN,
            "nl": DEFAULT_FINANCIAL_TERMS_NL,
        }
        if self.language not in vocabularies:
            raise ValueError("Configure financial_terms before scoring this language")
        return vocabularies[self.language]
