"""Extract page content and calculate message-and-tone features."""

import re
import time
from functools import lru_cache
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from app.scraping import public_urls

from .message_analysis_config import (
    BENEFIT_MARKERS,
    BOILERPLATE_MARKERS,
    CONTENT_SELECTORS,
    COOKIE_BUTTON_TEXTS,
    CUSTOMER_MARKERS,
    EMOTIONAL_MARKERS,
    FEATURE_MARKERS,
    FORMAL_MARKERS,
    FRIENDLY_MARKERS,
    IDLE_TIMEOUT_MS,
    LEAD_MAX_CHARS,
    LIFESTYLE_MARKERS,
    MAX_ATTEMPTS,
    MIN_LEAD_WORDS,
    MIN_WORDS,
    NAV_TIMEOUT_MS,
    PERSUASIVE_MARKERS,
    POST_LOAD_WAIT_MS,
    PRICE_MARKERS,
    PRODUCT_MARKERS,
    REMOVE_SELECTORS,
    REMOVE_UNLESS_CONTENT_SELECTORS,
    RETRY_DELAY_MS,
    SCALE_RANGES,
    SENTENCE_PATTERN,
    USER_AGENT,
    WORD_PATTERN,
)

SCROLL_JS = """async () => {
    await new Promise((resolve) => {
        let steps = 0;
        const timer = setInterval(() => {
            window.scrollBy(0, 500);
            steps += 1;
            const atBottom =
                window.scrollY + window.innerHeight >= document.body.scrollHeight;
            if (atBottom || steps >= 60) {
                clearInterval(timer);
                resolve();
            }
        }, 100);
    });
}"""

# Removes page noise without deleting the real content. Elements in the
# "guarded" list (header, footer, form, modal, ...) are kept when they contain
# the main content, sit inside it, or (on pages without <main>) hold the h1.
REMOVE_NOISE_JS = """([alwaysSelectors, guardedSelectors, contentSelectors]) => {
    const content = contentSelectors.join(",");
    const hasContent = document.querySelector(content) !== null;
    const isRoot = (element) =>
        element === document.documentElement || element === document.body;
    const isProtected = (element) =>
        element.closest(content) !== null ||
        element.querySelector(content) !== null ||
        (!hasContent && element.querySelector("h1") !== null);
    document.querySelectorAll(alwaysSelectors.join(",")).forEach((element) => {
        if (!isRoot(element)) element.remove();
    });
    document.querySelectorAll(guardedSelectors.join(",")).forEach((element) => {
        if (!isRoot(element) && !isProtected(element)) element.remove();
    });
}"""


def clean_text(text: str) -> str:
    """Normalize whitespace in extracted text."""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def count_words(text: str) -> int:
    return len(WORD_PATTERN.findall(text))


def shorten(text: str, limit: int = 200) -> str:
    """Cut long text so it stays readable."""
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


@lru_cache(maxsize=None)
def marker_pattern(markers: tuple[str, ...]) -> re.Pattern:
    """Compile one regex for a marker list.

    Markers of 3 characters or fewer match a whole word ("you", "je", "vie").
    Longer markers match from the start of a word, so inflections still count
    ("save" -> "saves", "bespaar" -> "bespaart").
    """
    parts = []
    for marker in sorted(set(markers), key=len, reverse=True):
        escaped = re.escape(marker.lower())
        parts.append(escaped + r"\b" if len(marker) <= 3 else escaped)
    return re.compile(r"\b(?:" + "|".join(parts) + ")")


def marker_score(text: str, markers: tuple[str, ...]) -> int:
    return len(marker_pattern(markers).findall(text.lower()))


def per_100_words(count: float, words: int) -> float:
    """Convert a raw count to hits per 100 words, so page length does not matter."""
    return 100 * count / max(words, 1)


def scale_score(value: float, low: float, high: float) -> int:
    if value <= low:
        return 1
    if value >= high:
        return 5
    return round(1 + 4 * (value - low) / (high - low))


def scaled(name: str, value: float) -> int:
    low, high = SCALE_RANGES[name]
    return scale_score(value, low, high)


def sentence_list(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_PATTERN.split(text) if part.strip()]


def is_boilerplate(text: str) -> bool:
    """Detect footnotes and legal text that is not a marketing message."""
    lowered = text.lower()
    return text.startswith("*") or any(
        marker in lowered for marker in BOILERPLATE_MARKERS
    )


def find_value_proposition(blocks: list[dict[str, str]]) -> str:
    """Return the lead text under the h1: the first two sentences of the first
    paragraph that is long enough and is not boilerplate."""
    h1_index = next((i for i, block in enumerate(blocks) if block["tag"] == "h1"), -1)
    paragraphs = [block["text"] for block in blocks if block["tag"] == "p"]
    after_h1 = [
        block["text"] for block in blocks[h1_index + 1 :] if block["tag"] == "p"
    ]
    for paragraph in after_h1 + paragraphs:
        lead = shorten(" ".join(sentence_list(paragraph)[:2]), LEAD_MAX_CHARS)
        if count_words(lead) >= MIN_LEAD_WORDS and not is_boilerplate(lead):
            return lead
    return ""


CONTEXT_DESTROYED = "Execution context was destroyed"


def _settle_and_retry(page: Page, action, retries: int = 2, delay_ms: int = 1_000):
    """Run a page action, retrying if a late client-side redirect destroys
    the JS execution context mid-call. This happens on pages that redirect
    (e.g. stripping a query string, or an A/B-test bounce) just after the
    "load" event, so the very first script we run after that lands mid-navigation.
    Once caught, we wait for the new page to settle and simply retry on it.
    """
    last_error: PlaywrightError | None = None
    for _ in range(retries + 1):
        try:
            return action()
        except PlaywrightError as error:
            if CONTEXT_DESTROYED not in str(error):
                raise
            last_error = error
            try:
                page.wait_for_load_state("load", timeout=NAV_TIMEOUT_MS)
            except PlaywrightError:
                pass
            page.wait_for_timeout(delay_ms)
    raise last_error


def _block_texts(locator) -> list[str]:
    """Inner text of every heading/paragraph under locator, in one JS call
    (a single evaluate_all is far less likely to race a mid-render redirect
    than several separate calls would be)."""
    texts = locator.locator("h1, h2, h3, h4, h5, h6, p").evaluate_all(
        "elements => elements.map(element => element.innerText || '')"
    )
    return [clean_text(text) for text in texts if clean_text(text)]


def select_main_content(page: Page):
    """Return the first content container with enough text, else the body."""
    for selector in CONTENT_SELECTORS:
        locator = page.locator(selector)
        if locator.count() > 0:
            candidate = locator.first
            words = count_words(
                " ".join(_settle_and_retry(page, lambda c=candidate: _block_texts(c)))
            )
            if words >= MIN_WORDS:
                return candidate, selector
    return page.locator("body").first, "body"


def dismiss_cookie_banner(page: Page) -> str:
    """Click the first matching consent button. Return its label, or ''."""
    for text in COOKIE_BUTTON_TEXTS:
        pattern = re.compile(rf"\b{re.escape(text)}", re.IGNORECASE)
        button = page.get_by_role("button", name=pattern)
        try:
            if button.count() and button.first.is_visible():
                label = clean_text(button.first.inner_text())
                button.first.click(timeout=3_000)
                page.wait_for_timeout(500)
                return label or text
        except PlaywrightError:
            continue
    return ""


def _render_attempt(url: str, wait_until: str, capture=None) -> dict[str, Any]:
    """One attempt at loading url and extracting content from it."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
                user_agent=USER_AGENT,
            )
            if capture:

                def public_request(route):
                    try:
                        public_urls.validate_public_url(route.request.url)
                    except ValueError:
                        route.abort()
                    else:
                        route.continue_()

                page.route("**/*", public_request)
            page.goto(url, wait_until=wait_until, timeout=NAV_TIMEOUT_MS)
            try:
                page.wait_for_load_state("networkidle", timeout=IDLE_TIMEOUT_MS)
            except PlaywrightError:
                pass  # some pages never go idle; continue with what has loaded
            page.wait_for_timeout(POST_LOAD_WAIT_MS)
            page.locator("body").wait_for(state="attached", timeout=15_000)
            cookie_button = _settle_and_retry(page, lambda: dismiss_cookie_banner(page))
            _settle_and_retry(page, lambda: page.evaluate(SCROLL_JS))
            page.wait_for_timeout(1_000)
            _settle_and_retry(page, lambda: page.evaluate("window.scrollTo(0, 0)"))
            artifact_id = capture(page) if capture else None
            _settle_and_retry(
                page,
                lambda: page.evaluate(
                    REMOVE_NOISE_JS,
                    [
                        list(REMOVE_SELECTORS),
                        list(REMOVE_UNLESS_CONTENT_SELECTORS),
                        list(CONTENT_SELECTORS),
                    ],
                ),
            )
            main, container = select_main_content(page)
            raw_blocks = _settle_and_retry(
                page,
                lambda: main.locator("h1, h2, h3, h4, h5, h6, p").evaluate_all(
                    "elements => elements.map(element => "
                    "({tag: element.tagName.toLowerCase(), text: element.innerText}))"
                ),
            )
            blocks = [
                {"tag": block["tag"], "text": clean_text(block["text"])}
                for block in raw_blocks
                if clean_text(block["text"])
            ]
            headings = [block["text"] for block in blocks if block["tag"] != "p"]
            paragraphs = [
                block["text"]
                for block in blocks
                if block["tag"] == "p" and count_words(block["text"]) >= 2
            ]
            bullet_lists = []
            list_texts = _settle_and_retry(
                page, lambda: main.locator("ul, ol").all_inner_texts()
            )
            for list_text in list_texts:
                cleaned = clean_text(list_text)
                if cleaned and count_words(cleaned) >= 2:
                    bullet_lists.append(cleaned)
            h1_texts = [block["text"] for block in blocks if block["tag"] == "h1"]
            headline = h1_texts[0] if h1_texts else (headings[0] if headings else "")

            # The page's own JS can mutate the DOM between calls (animations,
            # lazy hydration, ...), so a second, separate inner_text() read
            # can race and come back thinner than what the block extraction
            # above already captured. Use whichever read is richer.
            try:
                direct_text = clean_text(
                    _settle_and_retry(page, lambda: main.inner_text())
                )
            except PlaywrightError:
                direct_text = ""
            block_text = clean_text(
                " ".join([b["text"] for b in blocks] + bullet_lists)
            )
            text = (
                direct_text
                if count_words(direct_text) >= count_words(block_text)
                else block_text
            )

            source = {
                "page_title": clean_text(_settle_and_retry(page, lambda: page.title())),
                "container": container,
                "cookie_button": cookie_button,
                "headline": headline,
                "value_proposition": find_value_proposition(blocks),
                "headings": headings,
                "paragraphs": paragraphs,
                "bullet_lists": bullet_lists,
                "text": text,
            }
            if capture:
                source["artifact_id"] = artifact_id
                source["tables"] = main.locator("table").all_inner_texts()
                source["final_url"] = page.url
            return source
        finally:
            browser.close()


def render_page(url: str, capture=None) -> dict[str, Any]:
    """Render a page and extract the content used by the analysis.

    Retries up to MAX_ATTEMPTS times when a navigation/timeout error hits
    mid-extraction (e.g. "Execution context was destroyed" from a late
    redirect) or when the page comes back with too little text. From the
    2nd attempt onward it waits for the full "load" event instead of just
    "domcontentloaded", which tends to fix single-page apps whose content
    is still empty at DOM-ready time.
    """
    last_error: Exception | None = None
    last_source: dict[str, Any] | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        wait_until = "domcontentloaded" if attempt == 1 else "load"
        try:
            source = _render_attempt(url, wait_until, capture=capture)
        except (PlaywrightError, PlaywrightTimeoutError) as error:
            last_error = error
            print(f"  Attempt {attempt}/{MAX_ATTEMPTS} failed: {error}")
        else:
            last_source = source
            if has_enough_content(source):
                return source
            print(
                f"  Attempt {attempt}/{MAX_ATTEMPTS} loaded only "
                f"{count_words(source['text'])} words; retrying."
            )
        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY_MS / 1000)

    if last_source is not None:
        return last_source
    raise last_error or RuntimeError(f"Could not render {url}")


def has_enough_content(source: dict[str, Any]) -> bool:
    return count_words(source["text"]) >= MIN_WORDS


def summarize_message(source: dict[str, Any]) -> str:
    headline = source["headline"]
    if headline:
        return headline.rstrip(".!?") + "."
    lead = source["value_proposition"]
    if lead:
        first_sentence = sentence_list(lead)
        message = first_sentence[0] if first_sentence else lead
        return message.rstrip(".!?") + "."
    return ""


def calculate_features(source: dict[str, Any]) -> dict[str, Any]:
    """Score the page. Every score is based on hits per 100 words."""
    text = source["text"]
    words = count_words(text)
    sentences = sentence_list(text)
    average_sentence_length = words / max(len(sentences), 1)
    exclamations = per_100_words(text.count("!"), words)
    numbers = per_100_words(len(re.findall(r"\d+(?:[.,]\d+)?", text)), words)

    def density(markers: tuple[str, ...]) -> float:
        return per_100_words(marker_score(text, markers), words)

    rational_markers = tuple(dict.fromkeys(PRODUCT_MARKERS + FEATURE_MARKERS))
    raw = {
        "formal": density(FORMAL_MARKERS) + max(0, average_sentence_length - 15) / 5,
        "friendly": density(FRIENDLY_MARKERS) + exclamations,
        "persuasive": density(PERSUASIVE_MARKERS) + exclamations,
        "emotional": density(EMOTIONAL_MARKERS),
        "rational": density(rational_markers) + numbers,
        "customer": density(CUSTOMER_MARKERS),
        "product": density(PRODUCT_MARKERS),
        "feature": density(FEATURE_MARKERS),
        "benefit": density(BENEFIT_MARKERS),
        "lifestyle": density(LIFESTYLE_MARKERS),
        "price": density(PRICE_MARKERS),
    }
    focus_scores = {
        "Product": raw["product"],
        "Feature": raw["feature"],
        "Benefit": raw["benefit"],
        "Lifestyle": raw["lifestyle"],
        "Price": raw["price"],
    }
    focus = max(focus_scores, key=focus_scores.get)
    return {
        "words": words,
        "tone_formality": scaled("tone_formality", raw["formal"]),
        "tone_friendliness": scaled("tone_friendliness", raw["friendly"]),
        "tone_persuasiveness": scaled("tone_persuasiveness", raw["persuasive"]),
        "emotional_vs_rational": scaled(
            "emotional_vs_rational", raw["rational"] - raw["emotional"]
        ),
        "customer_vs_product_focus": scaled(
            "customer_vs_product_focus", raw["product"] - raw["customer"]
        ),
        "feature_vs_benefit_focus": scaled(
            "feature_vs_benefit_focus", raw["feature"] - raw["benefit"]
        ),
        "main_message": summarize_message(source),
        "value_proposition": source["value_proposition"],
        "message_focus": focus if focus_scores[focus] > 0 else "None",
        "raw_scores": {name: round(value, 2) for name, value in raw.items()},
    }
