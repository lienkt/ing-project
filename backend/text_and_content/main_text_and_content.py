"""
main.py
=======

Reads URLs from a plain text file (one URL per line) and runs the shared
`pipeline.py` against each one. Bank name and product name are derived
automatically from each URL (domain -> bank, last path segment -> product),
so no separate config file is needed — just list your URLs.

Expected input file (`url.txt`, one URL per line, "#" for comments):

    https://www.crelan.be/nl/particulieren/sparen-en-beleggen/sparen/product/spaarrekeningen
    https://www.argenta.be/nl/sparen/spaarrekening.html#waarom
    # this line is ignored
    https://www.ing.be/en/individuals/current-accounts-packs/youth-account

Usage:
    python main.py
    python main.py --file my_urls.txt
"""

import argparse
import asyncio
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from backend.text_and_content.pipeline_text_and_content import SiteConfig, run_pipeline


DEFAULT_URL_FILE = Path("url.txt")
OUTPUT_JSON = Path("bank_text_features.json")


# ============================================================================
# URL FILE PARSING
# ============================================================================

def resolve_url_file(path: Path) -> Path:
    """Accept either 'url.txt' or an extension-less file named 'url'."""
    if path.exists():
        return path

    alt = path.with_suffix("")  # e.g. "url.txt" -> "url"
    if alt.exists():
        return alt

    raise FileNotFoundError(
        f"Could not find '{path}' (or '{alt}'). "
        "Create a text file with one URL per line."
    )


def read_urls(path: Path) -> list:
    """Read one URL per line, ignoring blank lines and '#' comments."""
    path = resolve_url_file(path)

    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    return urls


def derive_bank_name(url: str) -> str:
    """Turn a domain like 'www.ing.be' into a readable bank name."""
    netloc = urlparse(url).netloc.lower()
    parts = [part for part in netloc.split(".") if part != "www"]
    name = parts[0] if parts else netloc
    return name.upper() if len(name) <= 3 else name.capitalize()


def derive_product_name(url: str) -> str:
    """Turn the last path segment into a readable product name."""
    path = urlparse(url).path
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return "Homepage"

    last = re.sub(r"\.\w+$", "", segments[-1])  # strip .html/.htm/etc.
    last = last.replace("-", " ").replace("_", " ").strip()
    return last.title() if last else "Homepage"


def derive_language(url: str) -> str:
    """Guess nl/en from a common language segment in the URL path."""
    path = urlparse(url).path.lower()
    if "/en/" in path or path.startswith("en/"):
        return "en"
    return "nl"


def build_site_config(url: str) -> SiteConfig:
    """Auto-build a SiteConfig from a bare URL (no manual per-site tuning)."""
    language = derive_language(url)
    return SiteConfig(
        bank=derive_bank_name(url),
        product=derive_product_name(url),
        url=url,
        language=language,
        locale="en-BE" if language == "en" else "nl-BE",
    )


# ============================================================================
# OUTPUT HELPERS
# ============================================================================

def print_result(result: dict) -> None:
    print()
    print("=" * 70)
    print(f"{result['bank']} — {result['product']}")
    print("=" * 70)
    print(f"URL: {result['url']}")
    print(f"1. word_count: {result['word_count']}")
    print(f"2. heading_count: {result['heading_count']}")
    print(f"3. paragraph_count: {result['paragraph_count']}")
    print(f"4. bullet_list_count: {result['bullet_list_count']}")
    print(f"5. average_paragraph_length: {result['average_paragraph_length']}")
    print(f"6. headline_length: {result['headline_length']}")
    print(f"7. text_density: {result['text_density']}")
    print(f"8. text_style: {result['text_style']}")
    print(f"9. information_complexity: {result['information_complexity']}")


def save_json(results: list) -> None:
    with OUTPUT_JSON.open("w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=4)
    print(f"\nSaved combined JSON → {OUTPUT_JSON}")


# ============================================================================
# MAIN
# ============================================================================

async def run(url_file: Path) -> None:
    urls = read_urls(url_file)
    print(f"Loaded {len(urls)} URL(s) from {url_file}")

    results = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        try:
            for url in urls:
                config = build_site_config(url)
                print(f"\nScraping {config.bank} ({config.product})...")
                try:
                    result = await run_pipeline(config, browser)
                except Exception as error:
                    print(f"  FAILED: {type(error).__name__}: {error}")
                    result = {
                        "bank": config.bank,
                        "product": config.product,
                        "url": config.url,
                        "error": str(error),
                    }

                results.append(result)

                if "error" not in result:
                    print_result(result)

        finally:
            await browser.close()

    save_json(results)
    print(f"\nDone. {sum('error' not in r for r in results)}/{len(results)} sites scraped successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape text features for a list of URLs.")
    parser.add_argument(
        "--file",
        default=str(DEFAULT_URL_FILE),
        help="Path to the text file with one URL per line (default: url.txt).",
    )
    args = parser.parse_args()

    asyncio.run(run(Path(args.file)))


if __name__ == "__main__":
    main()