import json
import re

from playwright.sync_api import sync_playwright


URL = "https://www.ing.be/en/individuals/current-accounts-packs/youth-account"
OUTPUT_JSON = "ing_youth_account_features.json"
WORD_PATTERN = re.compile(r"\w+")

HEADINGS_TO_IGNORE = (
    r"our products",
    r"ing belgium",
    r"our website",
    r"follow us",
    r"looking for",
    r"join thousands",
    r"financial independence",
    r"get ready",
    r"apply online",
    r"look out",
    r"cookie",
    r"privacy",
    r"terms",
    r"manage",
    r"need to",
    r"itsme",
    r"cash dispenser",
    r"savings account",
    r"ing save up",
    r"go to 18",
    r"is a youth account really free",
    r"can i open",
    r"who is the holder",
    r"how can i access",
    r"what level of control",
    r"does my child receive",
    r"carry your bank",
    r"replacement bank card",
    r"what happens if the debit card is lost or stolen",
    r"what happens when my child turns 18",
    r"also interesting",
)


def extract_headings(page):
    """Return all headings found through their ARIA role."""
    return page.get_by_role("heading").all_inner_texts()


def filter_real_headings(headings):
    """Keep product headings and remove navigation or FAQ headings."""
    cleaned_headings = []

    for heading in headings:
        heading = heading.strip()
        if not heading:
            continue

        if any(
            re.search(pattern, heading.lower())
            for pattern in HEADINGS_TO_IGNORE
        ):
            continue

        cleaned_headings.append(heading)

    return cleaned_headings


def scrape_page(url: str):
    """Load a page and extract its headings, paragraphs, and list items."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=60_000)
            page.wait_for_timeout(2_000)

            return {
                "headings": filter_real_headings(extract_headings(page)),
                "paragraphs": page.locator("p").all_inner_texts(),
                "bullet_lists": page.locator("ul li, ol li").all_inner_texts(),
            }
        finally:
            browser.close()


def count_words(text_list):
    return sum(len(WORD_PATTERN.findall(text)) for text in text_list)


def average_paragraph_length(paragraphs):
    if not paragraphs:
        return 0
    return count_words(paragraphs) / len(paragraphs)


def headline_length(headings):
    return len(WORD_PATTERN.findall(headings[0])) if headings else 0


def text_density(word_count):
    if word_count < 150:
        return 1
    if word_count < 300:
        return 2
    if word_count < 600:
        return 3
    if word_count < 1_000:
        return 4
    return 5


def text_style(average_length):
    if average_length < 15:
        return "Concise"
    if average_length < 35:
        return "Balanced"
    return "Detailed"


def information_complexity(word_count, heading_count):
    score = 1
    score += word_count > 300
    score += word_count > 600
    score += heading_count > 5
    return min(score, 5)


def extract_features(url):
    """Scrape a page and save one JSON document with all results."""
    data = scrape_page(url)

    headings = data["headings"]
    paragraphs = data["paragraphs"]
    bullet_lists = data["bullet_lists"]
    word_count = count_words(paragraphs)
    heading_count = len(headings)
    paragraph_count = len(paragraphs)
    average_length = average_paragraph_length(paragraphs)

    features = {
        "url": url,
        "word_count": word_count,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "bullet_list_count": len(bullet_lists),
        "average_paragraph_length": average_length,
        "headline_length": headline_length(headings),
        "text_density": text_density(word_count),
        "text_style": text_style(average_length),
        "information_complexity": information_complexity(
            word_count, heading_count
        ),
    }

    result = {
        **features,
        "source": {
            "headings": headings,
            "paragraphs": paragraphs,
            "bullet_lists": bullet_lists,
        },
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print(f"Saved JSON → {OUTPUT_JSON}")
    return result


if __name__ == "__main__":
    extract_features(URL)
