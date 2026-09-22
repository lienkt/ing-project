import asyncio
import json
import re

from playwright.async_api import async_playwright


URL = "https://www.beobank.be/nl/verzekeringen/mobiliteit/autoverzekering.html"

OUTPUT_JSON = "beobank_car_insurance_features.json"


def clean_text(text):
    """Normalize whitespace."""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_words(text):
    """Extract words, including Dutch characters and hyphenated words."""
    return re.findall(r"\b[\wÀ-ÿ]+(?:[-'][\wÀ-ÿ]+)*\b", text)


def count_words(text):
    return len(get_words(text))


async def load_page(page):
    """
    Open the page using a real Chromium browser.

    Playwright allows JavaScript to execute, so the extracted
    DOM represents the rendered page rather than only the
    initial server response.
    """

    print(f"Opening: {URL}\n")

    await page.goto(
        URL,
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    # Give dynamically loaded content some time to appear.
    await page.wait_for_timeout(3_000)

    # Scroll through the page to trigger lazy-loaded content.
    await page.evaluate(
        """
        async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 500;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if (
                        totalHeight >=
                        document.body.scrollHeight
                    ) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }
        """
    )

    # Give lazy-loaded elements time to finish rendering.
    await page.wait_for_timeout(2_000)

    # Return to the top.
    await page.evaluate("window.scrollTo(0, 0)")


async def clean_page(page):
    """
    Remove global elements that should not contribute to the
    text analysis.

    This is executed inside the browser DOM.
    """

    await page.evaluate(
        """
        () => {
            const selectors = [

                // JavaScript / styling
                'script',
                'style',
                'noscript',
                'template',
                'svg',
                'canvas',
                'iframe',

                // Global navigation
                'header',
                'footer',
                'nav',

                // Cookie / consent UI
                '[class*="cookie"]',
                '[id*="cookie"]',
                '[class*="consent"]',
                '[id*="consent"]',

                // Chatbots
                '[class*="chatbot"]',
                '[class*="chat-bot"]',
                '[id*="chatbot"]',
                '[id*="chat-bot"]',

                // Search / modal overlays
                '[class*="search-overlay"]',
                '[class*="modal"]',
                '[class*="overlay"]',
            ];

            document
                .querySelectorAll(selectors.join(','))
                .forEach((element) => {
                    element.remove();
                });
        }
        """
    )


async def find_main_selector(page):
    """
    Identify the main product-page container.

    Preference:
        1. main
        2. article
        3. [role=main]
        4. body
    """

    selectors = [
        "main",
        "article",
        '[role="main"]',
        "body",
    ]

    for selector in selectors:
        locator = page.locator(selector)
        if await locator.count() > 0:
            return selector

    return "body"


async def extract_headings(main):
    headings = []
    locator = main.locator("h1, h2, h3, h4, h5, h6")
    count = await locator.count()

    for index in range(count):
        element = locator.nth(index)
        if not await element.is_visible():
            continue

        text = clean_text(await element.inner_text())
        if not text:
            continue

        headings.append(text)

    return headings


async def extract_headline(main):
    h1 = main.locator("h1").first
    if await h1.count() == 0:
        return ""
    if not await h1.is_visible():
        return ""

    return clean_text(await h1.inner_text())


async def extract_paragraphs(main):
    paragraphs = []
    locator = main.locator("p")
    count = await locator.count()

    for index in range(count):
        element = locator.nth(index)
        if not await element.is_visible():
            continue

        text = clean_text(await element.inner_text())
        if not text:
            continue

        # Ignore extremely small UI fragments.
        if count_words(text) < 2:
            continue

        paragraphs.append(text)

    return paragraphs


async def extract_lists(main):
    lists = []
    locator = main.locator("ul, ol")
    count = await locator.count()

    for index in range(count):
        list_element = locator.nth(index)
        if not await list_element.is_visible():
            continue

        # Only direct LI children count.
        items_locator = list_element.locator(":scope > li")
        item_count = await items_locator.count()
        if item_count == 0:
            continue

        items = []
        for item_index in range(item_count):
            item = items_locator.nth(item_index)
            text = clean_text(await item.inner_text())
            if text:
                items.append(text)

        if items:
            list_type = await list_element.evaluate(
                "(el) => el.tagName.toLowerCase()"
            )
            lists.append({"type": list_type, "items": items})

    return lists


def build_content_text(headings, paragraphs, lists):
    """Combine extracted content in the same order used by the report."""
    lines = [*headings, *paragraphs]
    lines.extend(item for list_data in lists for item in list_data["items"])
    return "\n".join(lines)


def remove_duplicate_lines(text):
    """Remove blank lines and repeated content while preserving order."""
    unique_lines = []
    seen = set()

    for line in text.splitlines():
        line = clean_text(line)
        if line and line not in seen:
            seen.add(line)
            unique_lines.append(line)

    return "\n".join(unique_lines)


def calculate_text_density(
    word_count, heading_count, paragraph_count, bullet_list_count
):
    """Return a 1-5 score based on the amount and structure of text."""
    if word_count < 300:
        score = 1
    elif word_count < 700:
        score = 2
    elif word_count < 1200:
        score = 3
    elif word_count < 1800:
        score = 4
    else:
        score = 5

    has_dense_structure = (
        heading_count >= 10 and paragraph_count >= 25 and bullet_list_count >= 5
    )
    if has_dense_structure:
        score = min(5, score + 1)

    return score


def calculate_text_style(word_count, average_paragraph_length):
    if word_count >= 1500 or average_paragraph_length >= 45:
        return "Detailed"
    if word_count < 700:
        return "Concise"
    return "Balanced"


def calculate_information_complexity(text, heading_count, bullet_list_count):
    text_lower = text.lower()
    complexity_terms = [
        "verzekering",
        "verzekerings",
        "waarborg",
        "aansprakelijkheid",
        "uitsluiting",
        "beperking",
        "vrijstelling",
        "schadevergoeding",
        "schadegeval",
        "rechtsbijstand",
        "premie",
        "bestuurder",
        "contractvoorwaarden",
        "algemene voorwaarden",
        "bijzondere voorwaarden",
        "bonus-malus",
        "cataloguswaarde",
        "burgerlijke aansprakelijkheid",
        "recht van verhaal",
        "maximale toegestane massa",
    ]
    term_hits = sum(text_lower.count(term) for term in complexity_terms)

    # Detect monetary values and percentages.
    numeric_hits = len(re.findall(
        r"(€\s?[\d.,]+|[\d.,]+\s?€|\b\d+(?:[.,]\d+)?\s?%)",
        text,
        flags=re.IGNORECASE,
    ))

    words = count_words(text)
    score = 1
    score += words >= 700
    score += words >= 1400
    score += heading_count >= 10
    score += term_hits >= 20 or bullet_list_count >= 10
    score += numeric_hits >= 10
    return min(5, score)


async def extract_features(page):
    main_selector = await find_main_selector(page)
    print(f"Main content selector: {main_selector}")
    main = page.locator(main_selector).first

    headings = await extract_headings(main)
    paragraphs = await extract_paragraphs(main)
    lists = await extract_lists(main)
    headline = await extract_headline(main)

    content_text = remove_duplicate_lines(
        build_content_text(headings, paragraphs, lists)
    )
    total_words = count_words(content_text)
    total_headings = len(headings)
    total_paragraphs = len(paragraphs)
    total_lists = len(lists)
    average_paragraph_length = (
        sum(count_words(paragraph) for paragraph in paragraphs) / total_paragraphs
        if total_paragraphs
        else 0
    )

    features = {
        "url": URL,
        "word_count": total_words,
        "heading_count": total_headings,
        "paragraph_count": total_paragraphs,
        "bullet_list_count": total_lists,
        "average_paragraph_length": round(average_paragraph_length, 2),
        "headline_length": count_words(headline),
        "text_density": calculate_text_density(
            total_words, total_headings, total_paragraphs, total_lists
        ),
        "text_style": calculate_text_style(
            total_words, average_paragraph_length
        ),
        "information_complexity": calculate_information_complexity(
            content_text, total_headings, total_lists
        ),
    }

    return {
        **features,
        "source": {
            "headline": headline,
            "headings": headings,
            "paragraphs": paragraphs,
            "lists": lists,
            "text": content_text,
        },
    }

def save_json(features):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(features, file, ensure_ascii=False, indent=4)

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page(
            viewport={"width": 1440, "height": 900}, locale="nl-BE"
        )
        try:
            await load_page(page)
            print("Page loaded successfully.")
            await clean_page(page)
            print("Non-content elements removed.")
            features = await extract_features(page)
            save_json(features)
            print(f"\nSaved JSON → {OUTPUT_JSON}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())