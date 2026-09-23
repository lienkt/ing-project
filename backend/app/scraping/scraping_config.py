"""Browser settings, extraction options, and automatic scraping support.

Add message/tone cases to data/sources/messages.json. Dedicated handlers are
listed in _build_auto_support(). Unlisted sources still use generic capture.
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from app.schemas.automation import SourceDefinition, build_case_key
from app.scraping.feature_labels import label_ing_youth_account_en
from app.scraping.message_scraper import label_message_page, scrape_message_page
from app.scraping.page_scrapers import scrape_ing_youth_account_en

# Browser defaults and cleanup selectors.
COLLECTION_TIMEOUT_SECONDS = 120
LANGUAGE_LOCALES = {
    "English": ("en", "en-BE"),
    "Dutch": ("nl", "nl-BE"),
    "French": ("fr", "fr-BE"),
}

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


# Financial vocabulary for information-complexity scoring; tone rules live in
# message_analysis_config.py.
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


@dataclass
class SiteConfig:
    """Browser and extraction options for one source."""

    bank: str
    product: str
    url: str
    language: str = "nl"  # "nl" or "en" -> default vocabulary
    financial_terms: Iterable[str] | None = None
    heading_exclude: Iterable[str] = field(default_factory=tuple)
    paragraph_exclude: Iterable[str] = field(default_factory=tuple)
    bullet_exclude: Iterable[str] = field(default_factory=tuple)
    clean_page: bool = True
    public_only: bool = False
    main_selector: str | None = None
    ready_selector: str | None = None
    wait_ms: int = 3000
    viewport: dict = field(default_factory=lambda: {"width": 1440, "height": 1000})
    locale: str = "nl-BE"

    def terms(self) -> Iterable[str]:
        """Use explicit financial vocabulary, or the language default."""
        if self.financial_terms is not None:
            return self.financial_terms
        vocabularies = {
            "en": DEFAULT_FINANCIAL_TERMS_EN,
            "nl": DEFAULT_FINANCIAL_TERMS_NL,
        }
        if self.language not in vocabularies:
            raise ValueError("Configure financial_terms before scoring this language")
        return vocabularies[self.language]


# Automatic support: one entry contains both scraping and labeling handlers.
MESSAGE_SOURCES_PATH = (
    Path(__file__).resolve().parents[2] / "data/sources/messages.json"
)


def _build_auto_support() -> dict:
    """Load message cases without replacing dedicated product handlers."""
    support = {
        build_case_key("ING", "Current Account", "ING Youth Account", "EN"): {
            "scrape": scrape_ing_youth_account_en,
            "label": label_ing_youth_account_en,
        },
    }
    entries = json.loads(MESSAGE_SOURCES_PATH.read_text(encoding="utf-8"))["sources"]
    for entry in entries:
        source = SourceDefinition.model_validate(entry)
        key = build_case_key(
            source.bank, source.product_category, source.product_name, source.language
        )
        support.setdefault(
            key, {"scrape": scrape_message_page, "label": label_message_page}
        )
    return support


AUTO_SUPPORT = _build_auto_support()
