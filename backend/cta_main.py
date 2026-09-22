"""Run CTA extraction for every record in ``product_urls.json``."""

import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

import cta_config as config
from cta_function import extract_cta_features, normalize_input_url


FEATURE_FIELDS = (
    "cta_count",
    "primary_cta_text",
    "cta_above_fold",
    "cta_repeated",
    "cta_prominence",
    "cta_type",
)


def load_url_source(path: Path) -> list[dict[str, Any]]:
    """Load and validate the input records."""
    if not path.exists():
        raise FileNotFoundError(f"URL source JSON not found: {path.resolve()}")
    with path.open(encoding="utf-8") as source_file:
        records = json.load(source_file).get("urls")
    if not isinstance(records, list):
        raise ValueError('Input JSON must contain a top-level "urls" list.')
    return records


def build_result_row(record: dict[str, Any], url: str) -> dict[str, Any]:
    """Return the shared metadata for a URL extraction result."""
    return {
        "bank": record.get("bank", "Unknown"),
        "product_name": record.get("product_name", "Unknown"),
        "category": record.get("category", "Unknown"),
        "url": url,
    }


def add_error_result(row: dict[str, Any], error: Exception) -> None:
    """Populate an unsuccessful result row with a consistent feature schema."""
    row.update(dict.fromkeys(FEATURE_FIELDS))
    row.update(
        {
            "status": "error",
            "error": f"{type(error).__name__}: {error}",
        }
    )


def write_results(results: list[dict[str, Any]]) -> None:
    """Write public result fields, excluding operational status information."""
    output_rows = [
        {key: value for key, value in row.items() if key not in {"status", "error"}}
        for row in results
    ]
    with config.OUTPUT_FILE.open("w", encoding="utf-8") as output_file:
        json.dump({"results": output_rows}, output_file, ensure_ascii=False, indent=2)


async def run() -> None:
    """Extract CTA features, save results, and report progress."""
    results = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=config.HEADLESS)
        context = await browser.new_context(
            viewport=config.VIEWPORT,
            locale="en-GB",
            timezone_id="Europe/Brussels",
        )
        for record in load_url_source(config.URL_SOURCE_FILE):
            url = normalize_input_url(str(record.get("url", "")))
            row = build_result_row(record, url)
            page = await context.new_page()
            try:
                if not url.startswith(("http://", "https://")):
                    raise ValueError("Invalid or missing HTTP(S) URL")
                row.update(await extract_cta_features(page, url))
                row["status"] = "ok"
            except Exception as error:
                add_error_result(row, error)
            finally:
                await page.close()
            results.append(row)
            print(f"[{row['status'].upper()}] {row['bank']}: {url}")
        await browser.close()
    write_results(results)
    print(f"Saved {len(results)} results to {config.OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    asyncio.run(run())
