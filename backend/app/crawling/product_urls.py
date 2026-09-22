"""Build one product-only URL catalog from the sitemap URL collection.

Run from ``backend`` after crawling the bank sitemaps::

    python -m app.crawling.product_urls

The output is intentionally a single, flat JSON document so it can be used as
input to a scraper without having to iterate through one file per bank.
"""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_INPUT_FILE = DATA_DIR / "bank_urls.json"
DEFAULT_OUTPUT_FILE = DATA_DIR / "product_urls.json"

# These are URL path markers used by the Belgian banks in the sitemap data.
# The order matters: a mortgage is also a loan, so it must be classified first.
CATEGORY_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("mortgage", ("mortgage", "hypothe", "woonlening", "pret-immobilier")),
    (
        "credit_card",
        ("credit-card", "credit-cards", "kredietkaart", "kredietkaarten", "cartes-de-credit"),
    ),
    ("savings_account", ("saving", "savings", "sparen", "spaar", "epargn", "compte-epargne")),
    ("current_account", ("current-account", "current-accounts", "zichtrekening", "zichtrekeningen", "compte-a-vue", "comptes-bancaire")),
    ("insurance", ("insurance", "verzeker", "assurance")),
    ("investment", ("invest", "beleggen", "belegging", "placement")),
    ("personal_loan", ("borrowing", "loan", "lenen", "lening", "emprunter", "pret", "krediet", "credit")),
)

# A topic can contain a product word without being a product page (for example,
# a market-news story about investing).  Excluding these sitemap sections keeps
# the catalog useful for collection while retaining product landing pages.
NON_PRODUCT_SECTIONS = {
    "actu",
    "actualites",
    "blog",
    "contact",
    "faq",
    "fraud",
    "fraude",
    "news",
    "nieuws",
    "publication",
    "publications",
    "security",
    "securite",
}


def infer_language(url: str) -> str | None:
    """Infer the language when the URL uses a conventional language segment."""
    parts = [part.lower() for part in urlsplit(url).path.split("/") if part]
    for part in parts:
        if part in {"en", "nl", "fr"}:
            return part
    return None


def product_category(url: str) -> str | None:
    """Return a taxonomy category for a product URL, or ``None``."""
    path = urlsplit(url).path.lower()
    sections = {part for part in path.split("/") if part}
    if sections & NON_PRODUCT_SECTIONS:
        return None
    for category, markers in CATEGORY_MARKERS:
        if any(marker in path for marker in markers):
            return category
    return None


def extract_product_urls(bank_urls: dict[str, list[str]]) -> list[dict[str, str | None]]:
    """Return unique product URLs with their bank, category, and language."""
    products: list[dict[str, str | None]] = []
    seen: set[str] = set()
    for bank, urls in bank_urls.items():
        for url in urls:
            category = product_category(url)
            if category is None or url in seen:
                continue
            seen.add(url)
            products.append(
                {
                    "bank": bank,
                    "product_category": category,
                    "language": infer_language(url),
                    "url": url,
                }
            )
    return products


def write_product_urls(
    input_file: Path = DEFAULT_INPUT_FILE,
    output_file: Path = DEFAULT_OUTPUT_FILE,
) -> Path:
    """Extract product URLs from ``input_file`` and write one JSON catalog."""
    bank_urls = json.loads(input_file.read_text(encoding="utf-8"))
    products = extract_product_urls(bank_urls)
    payload = {
        "source": input_file.name,
        "total_urls": len(products),
        "urls_by_bank": dict(sorted(Counter(item["bank"] for item in products).items())),
        "urls_by_category": dict(sorted(Counter(item["product_category"] for item in products).items())),
        "products": products,
    }
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_file


def main() -> None:
    output_file = write_product_urls()
    print(f"Saved product URLs to {output_file}")


if __name__ == "__main__":
    main()
