

import asyncio
import json
import re

from playwright.async_api import async_playwright


URL = "https://www.argenta.be/nl/sparen/spaarrekening.html#waarom"

OUTPUT_JSON = "argenta_playwright_features.json"
OUTPUT_TEXT = "argenta_playwright_text.txt"

FINANCIAL_TERMS = (
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
)


# =============================================================================
# TEXT HELPERS
# =============================================================================

def normalize_text(text: str) -> str:
    """Normalize whitespace and return clean text."""
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def count_words(text: str) -> int:
    """Count words consistently, including accented characters."""
    if not text:
        return 0

    words = re.findall(
        r"\b[\wÀ-ÖØ-öø-ÿ]+(?:[-'][\wÀ-ÖØ-öø-ÿ]+)*\b",
        text,
        flags=re.UNICODE,
    )

    return len(words)


async def extract_visible_text(locator) -> list[str]:
    """Extract normalized text from visible elements."""
    results = []

    for index in range(await locator.count()):
        element = locator.nth(index)

        try:
            if not await element.is_visible():
                continue

            text = normalize_text(await element.inner_text())

            if text:
                results.append(text)

        except Exception:
            continue

    return results


# =============================================================================
# FEATURE CALCULATIONS
# =============================================================================

def calculate_text_density(
    word_count: int,
    heading_count: int,
    paragraph_count: int,
    bullet_list_count: int,
) -> int:
    """Calculate text density on a 1-5 scale."""
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

    structure_count = (
        heading_count
        + paragraph_count
        + bullet_list_count
    )

    if structure_count >= 35:
        score += 1

    return min(score, 5)


def calculate_text_style(
    word_count: int,
    average_paragraph_length: float,
    heading_count: int,
) -> str:
    """Classify the text as Concise, Balanced, or Detailed."""
    if (
        word_count < 500
        and average_paragraph_length < 60
    ):
        return "Concise"

    if (
        word_count >= 1000
        or average_paragraph_length >= 80
        or heading_count >= 15
    ):
        return "Detailed"

    return "Balanced"


def calculate_information_complexity(
    text: str,
    word_count: int,
    heading_count: int,
) -> int:
    """Calculate information complexity on a 1-5 scale."""
    lower_text = text.lower()
    score = 1

    # Length
    if word_count >= 400:
        score += 1

    if word_count >= 900:
        score += 1

    # Structure
    if heading_count >= 10:
        score += 1

    # Financial terminology
    matched_terms = sum(
        term in lower_text
        for term in FINANCIAL_TERMS
    )

    if matched_terms >= 3:
        score += 1

    # Percentages
    percentage_count = len(
        re.findall(
            r"\b\d+(?:[.,]\d+)?\s*%",
            text,
        )
    )

    if percentage_count >= 3:
        score += 1

    # Euro amounts
    euro_count = len(
        re.findall(
            r"(?:"
            r"€\s*[\d.,]+"
            r"|"
            r"[\d.,]+\s*€"
            r"|"
            r"EUR\s*[\d.,]+"
            r"|"
            r"[\d.,]+\s*EUR"
            r")",
            text,
            flags=re.IGNORECASE,
        )
    )

    if euro_count >= 3:
        score += 1

    return min(score, 5)


# =============================================================================
# PLAYWRIGHT SCRAPER
# =============================================================================

async def scroll_page(page) -> None:
    """Scroll through the page to trigger lazy-loaded content."""
    print("Scrolling page...")

    try:
        await page.evaluate(
            """
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 500;

                    const timer = setInterval(() => {
                        window.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= document.body.scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 200);
                });
            }
            """
        )

    except Exception as error:
        print("Scrolling warning:")
        print(error)


async def scrape_with_playwright():
    """Load the Argenta page and extract visible textual content."""
    print()
    print("=" * 70)
    print("STARTING PLAYWRIGHT")
    print("=" * 70)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        context = await browser.new_context(
            locale="nl-BE",
            timezone_id="Europe/Brussels",
            viewport={
                "width": 1440,
                "height": 1000,
            },
            user_agent=(
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/153.0.0.0 "
                "Safari/537.36"
            ),
        )

        page = await context.new_page()

        try:
            # Open page
            print("\nOpening:")
            print(URL)

            try:
                response = await page.goto(
                    URL,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )

            except Exception as error:
                print("\nNavigation error:")
                print(error)
                return None

            if response:
                print(f"HTTP status: {response.status}")

            # Wait for JavaScript-rendered content
            print("Waiting for JavaScript...")
            await page.wait_for_timeout(5000)

            # Wait for main content
            try:
                await page.locator("main").first.wait_for(
                    state="attached",
                    timeout=15_000,
                )
                print("Main element found.")

            except Exception:
                print("No <main> element found.")

            # Trigger lazy-loaded content
            await scroll_page(page)

            await page.wait_for_timeout(3000)

            # Return to top
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)

            # Select main content
            main_exists = await page.locator("main").count() > 0

            if main_exists:
                print("Using <main> as primary content.")

                main_locator = page.locator("main").first

            else:
                print("WARNING: <main> not found.")
                print("Using <body> as fallback.")

                main_locator = page.locator("body")

            main_html = await main_locator.inner_html()
            main_text = await main_locator.inner_text()

            # Rendered HTML
            rendered_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Rendered Argenta Main Content</title>
</head>
<body>
    {main_html}
</body>
</html>
""".strip()

            print(f"\nMain HTML characters: {len(main_html):,}")
            print(
                "Main visible text characters: "
                f"{len(main_text):,}"
            )

            # Extract visible elements
            print("\nExtracting visible elements...")

            headings = await extract_visible_text(
                main_locator.locator(
                    "h1, h2, h3, h4, h5, h6"
                )
            )

            headline = ""

            h1_locator = main_locator.locator("h1").first

            try:
                if (
                    await h1_locator.count() > 0
                    and await h1_locator.is_visible()
                ):
                    headline = normalize_text(
                        await h1_locator.inner_text()
                    )

            except Exception:
                headline = ""

            paragraphs = await extract_visible_text(
                main_locator.locator("p")
            )

            lists = await extract_visible_text(
                main_locator.locator("ul, ol")
            )

            tables = await extract_visible_text(
                main_locator.locator("table")
            )

            all_text = normalize_text(main_text)

            return {
                "html": rendered_html,
                "headline": headline,
                "headings": headings,
                "paragraphs": paragraphs,
                "lists": lists,
                "tables": tables,
                "all_text": all_text,
            }

        finally:
            await browser.close()


# =============================================================================
# FEATURE EXTRACTION
# =============================================================================

def calculate_features(content: dict) -> dict:
    """Calculate the nine text-analysis features."""
    print("\nCalculating 9 features...")

    word_count = count_words(content["all_text"])
    heading_count = len(content["headings"])
    paragraph_count = len(content["paragraphs"])
    bullet_list_count = len(content["lists"])

    if paragraph_count:
        paragraph_lengths = [
            count_words(paragraph)
            for paragraph in content["paragraphs"]
        ]

        average_paragraph_length = round(
            sum(paragraph_lengths) / paragraph_count,
            2,
        )

    else:
        average_paragraph_length = 0.0

    headline_length = count_words(content["headline"])

    text_density = calculate_text_density(
        word_count,
        heading_count,
        paragraph_count,
        bullet_list_count,
    )

    text_style = calculate_text_style(
        word_count,
        average_paragraph_length,
        heading_count,
    )

    information_complexity = calculate_information_complexity(
        content["all_text"],
        word_count,
        heading_count,
    )

    return {
        "url": URL,
        "word_count": word_count,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "bullet_list_count": bullet_list_count,
        "average_paragraph_length": average_paragraph_length,
        "headline_length": headline_length,
        "text_density": text_density,
        "text_style": text_style,
        "information_complexity": information_complexity,
    }


# =============================================================================
# OUTPUT
# =============================================================================

def save_json(features: dict) -> None:
    """Save calculated features as formatted JSON."""
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(
            features,
            file,
            ensure_ascii=False,
            indent=4,
        )

    print(f"JSON saved: {OUTPUT_JSON}")


def write_section(file, title: str) -> None:
    """Write a formatted section header."""
    file.write(f"{title}\n")
    file.write("=" * 70 + "\n")


def save_text(content: dict) -> None:
    """Save extracted content as a readable text file."""
    with open(OUTPUT_TEXT, "w", encoding="utf-8") as file:
        write_section(file, "URL")
        file.write(f"{URL}\n\n")

        write_section(file, "HEADLINE")
        file.write(f"{content['headline']}\n\n")

        write_section(file, "HEADINGS")

        for index, heading in enumerate(
            content["headings"],
            start=1,
        ):
            file.write(f"{index}. {heading}\n")

        file.write("\n")

        write_section(file, "PARAGRAPHS")

        for index, paragraph in enumerate(
            content["paragraphs"],
            start=1,
        ):
            file.write(f"{index}. {paragraph}\n\n")

        write_section(file, "LISTS")

        for index, item in enumerate(
            content["lists"],
            start=1,
        ):
            file.write(f"{index}. {item}\n\n")

        write_section(file, "TABLES")

        for index, table in enumerate(
            content["tables"],
            start=1,
        ):
            file.write(f"{index}. {table}\n\n")

        write_section(file, "ALL VISIBLE MAIN TEXT")
        file.write(content["all_text"])

    print(f"Text saved: {OUTPUT_TEXT}")


# =============================================================================
# CONSOLE RESULTS
# =============================================================================

def print_results(features: dict, content: dict) -> None:
    """Print the extracted features and content summary."""
    print()
    print("=" * 70)
    print("ARGENTA PLAYWRIGHT RESULTS")
    print("=" * 70)

    print(f"\nURL: {features['url']}\n")

    print(f"1. word_count: {features['word_count']}")
    print(f"2. heading_count: {features['heading_count']}")
    print(f"3. paragraph_count: {features['paragraph_count']}")
    print(f"4. bullet_list_count: {features['bullet_list_count']}")
    print(
        "5. average_paragraph_length: "
        f"{features['average_paragraph_length']}"
    )
    print(f"6. headline_length: {features['headline_length']}")
    print(f"7. text_density: {features['text_density']}")
    print(f"8. text_style: {features['text_style']}")
    print(
        "9. information_complexity: "
        f"{features['information_complexity']}"
    )

    print("\n" + "-" * 70)

    print(f"Headline: {content['headline']}")
    print(f"Headings extracted: {len(content['headings'])}")
    print(f"Paragraphs extracted: {len(content['paragraphs'])}")
    print(f"Lists extracted: {len(content['lists'])}")
    print(f"Tables extracted: {len(content['tables'])}")

    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================

async def main() -> None:
    """Run the scraper and save the results."""
    content = await scrape_with_playwright()

    if content is None:
        return

    features = calculate_features(content)

    save_json(features)
    save_text(content)
    print_results(features, content)


if __name__ == "__main__":
    asyncio.run(main())
