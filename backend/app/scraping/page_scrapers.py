"""Scraping functions receive SourceDefinition and return ScrapedPage.

Input includes campaign_id (None before import), bank, product_category,
product_name, language, URL, and stable source ID. Keep page.source unchanged.
Return success=False with error, or raise, on failure. Do not write to the DB.
Register supported cases in scraping_config.py; other sources use generic capture.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from playwright.async_api import Error, async_playwright

from app.schemas.automation import ScrapedPage, SourceDefinition, build_case_key
from app.scraping import capture, cta_analysis, public_urls
from app.scraping.message_analysis import clean_text, count_words

# scraping_config imports these handlers, so its runtime imports stay local.
if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

    from app.scraping.scraping_config import SiteConfig


logger = logging.getLogger(__name__)


def scrape_ing_youth_account_en(campaign: SourceDefinition) -> ScrapedPage:
    """ING / Current Account / ING Youth Account / EN only.

    Targets the product component verified in saved ING DOM evidence.
    Text completeness and collapsed FAQ still require review.
    """
    from app.scraping.scraping_config import SiteConfig

    expected = build_case_key("ING", "Current Account", "ING Youth Account", "EN")
    actual = build_case_key(
        campaign.bank,
        campaign.product_category,
        campaign.product_name,
        campaign.language,
    )
    if actual != expected:
        raise ValueError(
            "scrape_ing_youth_account_en only supports ING Youth Account EN"
        )
    config = SiteConfig(
        bank=campaign.bank,
        product=campaign.product_name,
        url=str(campaign.url),
        language="en",
        locale="en-BE",
        # ING body uses overlays-scroll-lock; scope reads instead of global cleanup.
        clean_page=False,
        main_selector="ing-feat-flexible-page",
        ready_selector="ing-feat-flexible-page flex-productheader h1",
    )
    return asyncio.run(_collect_page(campaign, config, _extract_ing_youth_account_en))


async def _extract_ing_youth_account_en(config: SiteConfig, browser) -> dict:
    """Case-owned extraction hook for ING Youth Account English.

    SiteConfig selects the product host rather than the layout main slot.
    Other product cases must supply their own extraction hook.
    """
    return await scrape_site(config, browser)


def capture_generic_page(campaign: SourceDefinition) -> ScrapedPage:
    """General evidence capture; never generates feature labels."""
    from app.scraping.scraping_config import LANGUAGE_LOCALES, SiteConfig

    public_urls.validate_public_url(str(campaign.url))
    language, locale = LANGUAGE_LOCALES.get(campaign.language, ("en", "en-BE"))
    config = SiteConfig(
        bank=campaign.bank,
        product=campaign.product_name,
        url=str(campaign.url),
        language=language,
        locale=locale,
        clean_page=False,
        public_only=True,
    )
    page = asyncio.run(_collect_page(campaign, config, scrape_site, allow_empty=True))
    page.metadata["collector"] = "playwright-generic-v1"
    page.warnings.append(
        "Generic capture only: no automatic labels. Navigation, cookie banners, or collapsed content may affect extraction."
    )
    if not page.text.strip():
        page.warnings.append(
            "No readable text extracted; review the saved screenshot and DOM."
        )
    return page


# Shared infrastructure: never register this helper directly in AUTO_SUPPORT.
async def _collect_page(
    campaign: SourceDefinition, config: SiteConfig, extractor, allow_empty=False
) -> ScrapedPage:
    """Manage browser resources and convert a case extractor's content to a snapshot."""

    from app.scraping.scraping_config import COLLECTION_TIMEOUT_SECONDS

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            content = await asyncio.wait_for(
                extractor(config, browser), timeout=COLLECTION_TIMEOUT_SECONDS
            )
        finally:
            await browser.close()
    if not allow_empty and not content["all_text"].strip():
        raise ValueError("No usable product text was extracted")
    return ScrapedPage(
        source=campaign,
        title=content["headline"] or campaign.product_name,
        headline=content["headline"],
        text=content["all_text"],
        headings=content["headings"],
        paragraphs=content["paragraphs"],
        bullets=content["bullets"],
        tables=content["tables"],
        bullet_list_count=content["bullet_list_count"],
        metadata={
            "collector": "playwright-text-v2",
            "final_url": content["final_url"],
            **(
                {"cta_features": json.dumps(content["cta_features"])}
                if "cta_features" in content
                else {}
            ),
            **(
                {"cta_warning": content["cta_warning"]}
                if "cta_warning" in content
                else {}
            ),
            **(
                {"artifact_id": content["artifact_id"]}
                if "artifact_id" in content
                else {}
            ),
        },
        scraped_at=datetime.now(UTC),
        warnings=[
            "Text extraction requires review. Screenshot and DOM evidence are stored when available; image, button and link counts are not measured. Cookie banners and collapsed sections may remain in the capture."
        ],
    )


def matches_any(text: str, patterns: Iterable[str]) -> bool:
    """True if any regex pattern (case-insensitive) is found in text."""
    if not patterns:
        return False
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def deduplicate_lines(lines: Iterable[str]) -> list[str]:
    """Remove blank/duplicate lines while preserving order."""
    seen = set()
    unique: list[str] = []
    for line in lines:
        cleaned = clean_text(line)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


async def scroll_page(page: Page) -> None:
    """Scroll to the bottom in steps to trigger lazy-loaded content."""

    try:
        await page.evaluate(
            """
            async () => {
                await new Promise((resolve) => {
                    let total = 0;
                    let steps = 0;
                    const step = 500;
                    const timer = setInterval(() => {
                        window.scrollBy(0, step);
                        total += step;
                        steps += 1;
                        if (total >= document.body.scrollHeight || steps >= 80) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 150);
                });
            }
            """
        )
    except Error:
        logger.debug("Optional page extraction step failed", exc_info=True)


async def load_page(
    page: Page, url: str, wait_ms: int = 3000, timeout_ms: int = 60_000
) -> None:
    """Open a URL, wait for JS content, scroll to trigger lazy-loading, return to top."""
    response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    if response is None or response.status >= 400:
        raise ValueError(
            f"Page load failed: HTTP {response.status if response else 'no response'}"
        )
    await page.wait_for_timeout(wait_ms)
    await scroll_page(page)
    await page.wait_for_timeout(1500)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)


async def remove_noise(page: Page) -> None:
    """Strip global chrome (nav/header/footer/cookie/chat/modal) from the DOM."""
    from app.scraping.scraping_config import NOISE_SELECTORS

    selector_list = ",".join(NOISE_SELECTORS)
    await page.evaluate(
        """(selectors) => {
            document.querySelectorAll(selectors).forEach((el) => {
                if (el !== document.body && el !== document.documentElement) el.remove();
            });
        }""",
        selector_list,
    )


async def find_main_locator(page: Page) -> Locator:
    """Prefer <main>, then <article>, then [role=main], else fall back to <body>."""
    for selector in ("main", "article", '[role="main"]'):
        locator = page.locator(selector)
        if await locator.count() > 0:
            return locator.first
    return page.locator("body")


# ============================================================================
# GENERIC CONTENT EXTRACTION
# ============================================================================


async def extract_visible_texts(locator: Locator) -> list[str]:
    """Return normalized inner_text for every visible match of a locator."""

    texts: list[str] = []
    count = await locator.count()
    for index in range(count):
        element = locator.nth(index)
        try:
            if not await element.is_visible():
                continue
            text = clean_text(await element.inner_text())
            if text:
                texts.append(text)
        except Error:
            logger.debug("Skipping unavailable page element", exc_info=True)
            continue
    return texts


async def extract_headline(main: Locator) -> str:

    h1 = main.locator("h1").first
    try:
        if await h1.count() > 0 and await h1.is_visible():
            return clean_text(await h1.inner_text())
    except Error:
        logger.debug("Optional page extraction step failed", exc_info=True)
    return ""


async def extract_content(
    main: Locator,
    heading_exclude: Iterable[str] = (),
    paragraph_exclude: Iterable[str] = (),
    bullet_exclude: Iterable[str] = (),
    min_paragraph_words: int = 2,
    min_bullet_chars: int = 5,
) -> dict:
    """Extract headline/headings/paragraphs/bullets/tables, applying per-site filters."""
    headline = await extract_headline(main)

    headings = [
        h
        for h in await extract_visible_texts(main.locator("h1, h2, h3, h4, h5, h6"))
        if not matches_any(h, heading_exclude)
    ]

    paragraphs = [
        p
        for p in await extract_visible_texts(main.locator("p"))
        if count_words(p) >= min_paragraph_words
        and not matches_any(p, paragraph_exclude)
    ]

    bullets = [
        b
        for b in await extract_visible_texts(main.locator("ul li, ol li"))
        if len(b) > min_bullet_chars and not matches_any(b, bullet_exclude)
    ]

    # Individual bullet items are filtered above, but bullet_list_count counts
    # the <ul>/<ol> containers themselves (matches the original per-bank scripts).
    bullet_list_count = await main.locator("ul, ol").count()

    tables = await extract_visible_texts(main.locator("table"))

    return {
        "headline": headline,
        "headings": headings,
        "paragraphs": paragraphs,
        "bullets": bullets,
        "bullet_list_count": bullet_list_count,
        "tables": tables,
    }


async def scrape_site(config: SiteConfig, browser) -> dict:
    """Load a page with Playwright and return its raw extracted content."""
    context = await browser.new_context(
        locale=config.locale,
        timezone_id="Europe/Brussels",
        viewport=config.viewport,
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
        ),
    )
    try:
        if config.public_only:

            async def public_requests(route):
                try:
                    await asyncio.to_thread(validate_public_url, route.request.url)
                except ValueError:
                    await route.abort()
                else:
                    await route.continue_()

            await context.route("**/*", public_requests)
        page = await context.new_page()
        await load_page(page, config.url, wait_ms=config.wait_ms)
        if config.ready_selector:
            await page.locator(config.ready_selector).first.wait_for(
                state="visible", timeout=30_000
            )

        artifact_id = await capture.capture_evidence(page)

        cta_data = {}
        try:
            cta_data["cta_features"] = await cta_analysis.extract_loaded_cta_features(
                page
            )
        except Exception as error:
            logger.warning("CTA extraction failed: %s", error)
            cta_data["cta_warning"] = (
                "CTA extraction failed; review CTA fields manually."
            )
        if config.clean_page:
            await remove_noise(page)
        main = (
            page.locator(config.main_selector).first
            if config.main_selector
            else await find_main_locator(page)
        )

        content = await extract_content(
            main,
            heading_exclude=config.heading_exclude,
            paragraph_exclude=config.paragraph_exclude,
            bullet_exclude=config.bullet_exclude,
        )

        all_text_lines = deduplicate_lines(
            [
                content["headline"],
                *content["headings"],
                *content["paragraphs"],
                *content["bullets"],
            ]
        )
        content["all_text"] = " ".join(all_text_lines)
        content["final_url"] = page.url
        content.update(cta_data)
        content["artifact_id"] = artifact_id
        return content
    finally:
        await context.close()
