"""
pipeline.py
===========

Shared scraping + feature-extraction pipeline for bank product pages.

This module holds everything that should behave IDENTICALLY across banks,
so the resulting scores are actually comparable to each other:

    - text normalization / word counting
    - a generic Playwright-based page loader (goto, wait, scroll, clean up)
    - generic content extraction (headline, headings, paragraphs, lists, tables)
    - the 9 standardized text-analysis features

Per-bank differences (URL, product name, site-specific noise patterns,
domain vocabulary) live in `main.py` as `SiteConfig` objects. `main.py`
loops over those configs and calls `run_pipeline()` for each one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from playwright.async_api import Locator, Page


# ============================================================================
# TEXT HELPERS
# ============================================================================

WORD_PATTERN = re.compile(r"\b[\wÀ-ÖØ-öø-ÿ]+(?:[-'][\wÀ-ÖØ-öø-ÿ]+)*\b", re.UNICODE)


def normalize_text(text: str) -> str:
    """Collapse whitespace / non-breaking spaces into one clean string."""
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def count_words(text: str) -> int:
    """Count words, including accented characters and hyphenated/contracted words."""
    if not text:
        return 0
    return len(WORD_PATTERN.findall(text))


def matches_any(text: str, patterns: Iterable[str]) -> bool:
    """True if any regex pattern (case-insensitive) is found in text."""
    if not patterns:
        return False
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def deduplicate_lines(lines: Iterable[str]) -> List[str]:
    """Remove blank/duplicate lines while preserving order."""
    seen = set()
    unique: List[str] = []
    for line in lines:
        cleaned = normalize_text(line)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


# ============================================================================
# DEFAULT FINANCIAL VOCABULARY (used for information_complexity)
# ============================================================================

DEFAULT_FINANCIAL_TERMS_NL = (
    "rente", "rentevoet", "interest", "interestvoet", "basisrente",
    "getrouwheidspremie", "spaarrekening", "spaarrekeningen", "belasting",
    "belastingen", "roerende voorheffing", "deposito", "depositobescherming",
    "garantiefonds", "voorwaarden", "voorwaarde", "kosten", "risico",
    "fiscale", "fiscaliteit", "minimum", "maximum", "vergoeding",
    "premie", "waarborg", "aansprakelijkheid", "uitsluiting", "vrijstelling",
    "schadevergoeding", "kredietopening",
)

DEFAULT_FINANCIAL_TERMS_EN = (
    "interest", "interest rate", "savings account", "fee", "fees",
    "conditions", "terms", "deposit", "deposit protection", "guarantee scheme",
    "minimum", "maximum", "tax", "withholding tax", "risk", "reward",
    "loan", "repayment", "apr", "premium", "insurance", "cover", "excess",
)


# ============================================================================
# GENERIC PAGE LOADING (Playwright)
# ============================================================================

NOISE_SELECTORS = (
    "script", "style", "noscript", "template", "svg", "canvas", "iframe",
    "header", "footer", "nav",
    '[class*="cookie"]', '[id*="cookie"]',
    '[class*="consent"]', '[id*="consent"]',
    '[class*="chatbot"]', '[class*="chat-bot"]',
    '[id*="chatbot"]', '[id*="chat-bot"]',
    '[class*="search-overlay"]', '[class*="modal"]', '[class*="overlay"]',
)


async def scroll_page(page: Page) -> None:
    """Scroll to the bottom in steps to trigger lazy-loaded content."""
    try:
        await page.evaluate(
            """
            async () => {
                await new Promise((resolve) => {
                    let total = 0;
                    const step = 500;
                    const timer = setInterval(() => {
                        window.scrollBy(0, step);
                        total += step;
                        if (total >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 150);
                });
            }
            """
        )
    except Exception:
        pass


async def load_page(page: Page, url: str, wait_ms: int = 3000, timeout_ms: int = 60_000) -> None:
    """Open a URL, wait for JS content, scroll to trigger lazy-loading, return to top."""
    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    await page.wait_for_timeout(wait_ms)
    await scroll_page(page)
    await page.wait_for_timeout(1500)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)


async def remove_noise(page: Page) -> None:
    """Strip global chrome (nav/header/footer/cookie/chat/modal) from the DOM."""
    selector_list = ",".join(NOISE_SELECTORS)
    await page.evaluate(
        """(selectors) => {
            document.querySelectorAll(selectors).forEach((el) => el.remove());
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

async def extract_visible_texts(locator: Locator) -> List[str]:
    """Return normalized inner_text for every visible match of a locator."""
    texts: List[str] = []
    count = await locator.count()
    for index in range(count):
        element = locator.nth(index)
        try:
            if not await element.is_visible():
                continue
            text = normalize_text(await element.inner_text())
            if text:
                texts.append(text)
        except Exception:
            continue
    return texts


async def extract_headline(main: Locator) -> str:
    h1 = main.locator("h1").first
    try:
        if await h1.count() > 0 and await h1.is_visible():
            return normalize_text(await h1.inner_text())
    except Exception:
        pass
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
        h for h in await extract_visible_texts(main.locator("h1, h2, h3, h4, h5, h6"))
        if not matches_any(h, heading_exclude)
    ]

    paragraphs = [
        p for p in await extract_visible_texts(main.locator("p"))
        if count_words(p) >= min_paragraph_words and not matches_any(p, paragraph_exclude)
    ]

    bullets = [
        b for b in await extract_visible_texts(main.locator("ul li, ol li"))
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


# ============================================================================
# STANDARDIZED FEATURE CALCULATIONS (applied identically to every bank)
# ============================================================================

def calculate_text_density(
    word_count: int, heading_count: int, paragraph_count: int, bullet_list_count: int
) -> int:
    """1-5 scale, driven by word count with a bonus for very dense structure."""
    if word_count < 200:
        score = 1
    elif word_count < 500:
        score = 2
    elif word_count < 900:
        score = 3
    elif word_count < 1400:
        score = 4
    else:
        score = 5

    structure_count = heading_count + paragraph_count + bullet_list_count
    if structure_count >= 35:
        score += 1

    return min(score, 5)


def calculate_text_style(word_count: int, average_paragraph_length: float, heading_count: int) -> str:
    """Concise / Balanced / Detailed classification."""
    if word_count < 500 and average_paragraph_length < 60:
        return "Concise"
    if word_count >= 1000 or average_paragraph_length >= 80 or heading_count >= 15:
        return "Detailed"
    return "Balanced"


def calculate_information_complexity(
    text: str, word_count: int, heading_count: int, financial_terms: Iterable[str]
) -> int:
    """1-5 scale based on length, structure, banking vocabulary, %, and € amounts."""
    lower_text = text.lower()
    score = 1

    if word_count >= 400:
        score += 1
    if word_count >= 900:
        score += 1
    if heading_count >= 10:
        score += 1

    matched_terms = sum(term.lower() in lower_text for term in financial_terms)
    if matched_terms >= 3:
        score += 1

    percentage_count = len(re.findall(r"\b\d+(?:[.,]\d+)?\s*%", text))
    if percentage_count >= 3:
        score += 1

    euro_count = len(re.findall(
        r"(?:€\s*[\d.,]+|[\d.,]+\s*€|EUR\s*[\d.,]+|[\d.,]+\s*EUR)", text, re.IGNORECASE
    ))
    if euro_count >= 3:
        score += 1

    return min(score, 5)


# ============================================================================
# SITE CONFIG
# ============================================================================

@dataclass
class SiteConfig:
    """Everything that is allowed to differ between banks."""

    bank: str
    product: str
    url: str
    language: str = "nl"                      # "nl" or "en" -> default vocabulary
    financial_terms: Optional[Iterable[str]] = None
    heading_exclude: Iterable[str] = field(default_factory=tuple)
    paragraph_exclude: Iterable[str] = field(default_factory=tuple)
    bullet_exclude: Iterable[str] = field(default_factory=tuple)
    wait_ms: int = 3000
    viewport: dict = field(default_factory=lambda: {"width": 1440, "height": 1000})
    locale: str = "nl-BE"

    def terms(self) -> Iterable[str]:
        if self.financial_terms is not None:
            return self.financial_terms
        return DEFAULT_FINANCIAL_TERMS_EN if self.language == "en" else DEFAULT_FINANCIAL_TERMS_NL


# ============================================================================
# ORCHESTRATION
# ============================================================================

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
    page = await context.new_page()
    try:
        await load_page(page, config.url, wait_ms=config.wait_ms)
        await remove_noise(page)
        main = await find_main_locator(page)

        content = await extract_content(
            main,
            heading_exclude=config.heading_exclude,
            paragraph_exclude=config.paragraph_exclude,
            bullet_exclude=config.bullet_exclude,
        )

        all_text_lines = deduplicate_lines(
            [content["headline"], *content["headings"], *content["paragraphs"], *content["bullets"]]
        )
        content["all_text"] = " ".join(all_text_lines)
        return content
    finally:
        await context.close()


def build_features(config: SiteConfig, content: dict) -> dict:
    """Compute the 9 standardized features plus identifying metadata."""
    word_count = count_words(content["all_text"])
    heading_count = len(content["headings"])
    paragraph_count = len(content["paragraphs"])
    bullet_list_count = content["bullet_list_count"]

    paragraph_lengths = [count_words(p) for p in content["paragraphs"]]
    average_paragraph_length = (
        round(sum(paragraph_lengths) / paragraph_count, 2) if paragraph_count else 0.0
    )

    headline_length = count_words(content["headline"])

    return {
        "bank": config.bank,
        "product": config.product,
        "url": config.url,
        "word_count": word_count,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "bullet_list_count": bullet_list_count,
        "average_paragraph_length": average_paragraph_length,
        "headline_length": headline_length,
        "text_density": calculate_text_density(
            word_count, heading_count, paragraph_count, bullet_list_count
        ),
        "text_style": calculate_text_style(
            word_count, average_paragraph_length, heading_count
        ),
        "information_complexity": calculate_information_complexity(
            content["all_text"], word_count, heading_count, config.terms()
        ),
    }


async def run_pipeline(config: SiteConfig, browser) -> dict:
    """Scrape one site and return its feature dict (with bank/product/url) + raw source."""
    content = await scrape_site(config, browser)
    features = build_features(config, content)
    return {
        **features,
        "source": {
            "headline": content["headline"],
            "headings": content["headings"],
            "paragraphs": content["paragraphs"],
            "bullets": content["bullets"],
        },
    }