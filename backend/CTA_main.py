"""
Run CTA extraction for all bank URLs in product_urls.json.

Input:
    product_urls.json

Output:
    cta_features.json
"""

import asyncio
import json

from pathlib import Path
from typing import Any, Dict, List

from playwright.async_api import (
    async_playwright,
)

import CTA_config as config

from CTA_function import (
    extract_cta_features,
    normalize_input_url,
)


# ============================================================
# LOAD URL SOURCE
# ============================================================

def load_url_source(
    path: Path,
) -> List[Dict[str, Any]]:
    """
    Load bank URLs from product_urls.json.
    """

    if not path.exists():

        raise FileNotFoundError(
            f"URL source JSON not found: "
            f"{path.resolve()}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        payload = json.load(file)

    urls = payload.get(
        "urls"
    )

    if not isinstance(
        urls,
        list,
    ):

        raise ValueError(
            'Input JSON must contain '
            'a top-level "urls" list.'
        )

    return urls


# ============================================================
# MAIN RUNNER
# ============================================================

async def run() -> None:
    """
    Run CTA extraction for every bank URL.
    """

    records = load_url_source(
        config.URL_SOURCE_FILE
    )

    results = []

    # --------------------------------------------------------
    # Start Playwright
    # --------------------------------------------------------

    async with async_playwright() as playwright:

        browser = await playwright.chromium.launch(
            headless=config.HEADLESS
        )

        context = await browser.new_context(

            viewport=config.VIEWPORT,

            locale="en-GB",

            # Helps pages that behave differently depending
            # on timezone / browser settings.
            timezone_id="Europe/Brussels",

        )

        # ----------------------------------------------------
        # Process every URL
        # ----------------------------------------------------

        for record in records:

            bank = record.get(
                "bank",
                "Unknown",
            )

            source_url = normalize_input_url(
                str(
                    record.get(
                        "url",
                        "",
                    )
                )
            )

            row = {

                "bank": bank,

                "source_file": record.get(
                    "source_file"
                ),

                "url": source_url,
            }

            page = await context.new_page()

            try:

                # --------------------------------------------
                # Validate URL
                # --------------------------------------------

                if not source_url.startswith(
                    (
                        "http://",
                        "https://",
                    )
                ):

                    raise ValueError(
                        "Invalid or missing "
                        "HTTP(S) URL"
                    )

                # --------------------------------------------
                # Extract CTA features
                # --------------------------------------------

                features = await extract_cta_features(
                    page,
                    source_url,
                )

                row.update(
                    features
                )

                row["status"] = "ok"

            except Exception as exc:

                row.update({

                    "cta_count": None,

                    "primary_cta_text": None,

                    "cta_above_fold": None,

                    "cta_repeated": None,

                    "cta_prominence": None,

                    "cta_type": None,

                    "status": "error",

                    "error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                })

            finally:

                await page.close()

            results.append(
                row
            )

            # ------------------------------------------------
            # Console output
            # ------------------------------------------------

            print(
                f"[{row['status'].upper()}] "
                f"{bank}: {source_url}"
            )

            if (
                row["status"] == "ok"
                and row.get("primary_cta_text")
            ):

                print(
                    "    Primary CTA: "
                    f"{row['primary_cta_text']}"
                )

                print(
                    "    Type: "
                    f"{row['cta_type']}"
                )

                print(
                    "    Above fold: "
                    f"{row['cta_above_fold']}"
                )

                print(
                    "    Prominence: "
                    f"{row['cta_prominence']}/5"
                )

        # ----------------------------------------------------
        # Close browser
        # ----------------------------------------------------

        await context.close()
        await browser.close()

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    config.OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with config.OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "results": results
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    successful = sum(
        1
        for row in results
        if row.get("status") == "ok"
    )

    failed = len(results) - successful

    print()
    print("=" * 60)
    print("CTA EXTRACTION COMPLETE")
    print("=" * 60)

    print(
        f"Total pages: {len(results)}"
    )

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Output: "
        f"{config.OUTPUT_FILE.resolve()}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(run())