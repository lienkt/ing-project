import json
import re

from playwright.sync_api import sync_playwright


URL = (
    "https://www.kbc.be/retail/en/loans/vehicle/"
    "car-loan.html?zone=more-services"
)
OUTPUT_JSON = "kbc_car_loan_features.json"
WORD_PATTERN = re.compile(r"\w+")

# ============================================================
# UNIFIED EXCLUSION LIST (KBC VERSION) — still used as a
# secondary safety net on top of the structural filter below
# ============================================================
EXCLUDE_TEXT = (
    r"language choice",
    r"private persons",
    r"businesses",
    r"private banking",
    r"commercial banking",
    r"all websites",
    r"contact",
    r"login",
    r"menu",
    r"skip to main content",
    r"back to the menu",
    r"^payments$",
    r"^savings$",
    r"^investments$",
    r"^loans$",
    r"^insurance$",
    r"^myhome$",
    r"^mymobility$",
    r"day-to-day banking",
    r"100% digital",
    r"other people also viewed",
    r"for businesses",
    r"show more",
    r"current accounts",
    r"payment cards",
    r"savings accounts",
    r"pension saving",
    r"long-term saving",
    r"for your home",
    r"for your vehicle",
    r"for other purposes",
    r"insuring your home",
    r"insuring your vehicle",
    r"insuring yourself or your family",
    r"discover our full offering",
    r"a question\? contact us",
    r"about us",
    r"other websites",
    r"sitemap",
    r"kbc group",
    r"press room",
    r"rates and charges",
    r"legal information",
    r"unsubscribe",
    r"jobs",
    r"responsible disclosure",
    r"accessibility",
    r"follow kbc on",
    r"share page by e-mail",
    r"we value your opinion",
    r"^home$",
    r"overview of loans",
)


# ============================================================
# HEADINGS
# ============================================================
def extract_headings(page):
    """Extract headings from h1-h3 elements."""
    return [
        heading
        for level in range(1, 4)
        for heading in page.locator(f"h{level}").all_inner_texts()
    ]


def filter_headings(headings):
    """Remove empty and navigation-related headings."""
    cleaned_headings = []

    for heading in headings:
        heading = heading.strip()
        if not heading:
            continue
        if any(re.search(pattern, heading.lower()) for pattern in EXCLUDE_TEXT):
            continue
        cleaned_headings.append(heading)

    return cleaned_headings


# ============================================================
# SCRAPER
# ============================================================
def scrape_page(url: str):
    """Load a page and extract filtered headings, paragraphs, and bullets."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            page.goto(url, timeout=60_000)
            page.wait_for_timeout(2_000)

            paragraphs = [
                paragraph.strip()
                for paragraph in page.locator("p").all_inner_texts()
                if paragraph.strip()
                and not any(
                    re.search(pattern, paragraph.lower())
                    for pattern in EXCLUDE_TEXT
                )
            ]

            bullets = []
            list_items = page.locator("ul li, ol li")
            for index in range(list_items.count()):
                item = list_items.nth(index)

                # Menu items are links or live inside site chrome.
                in_site_chrome = item.evaluate(
                    "el => !!el.closest('nav, header, footer, [role=navigation], "
                    "[class*=menu], [class*=nav], [class*=footer], [class*=breadcrumb]')"
                )
                if in_site_chrome or item.locator("a").count() > 0:
                    continue

                text = item.inner_text().strip()
                if not text or len(text) <= 5:
                    continue
                if any(
                    re.search(pattern, text.lower())
                    for pattern in EXCLUDE_TEXT
                ):
                    continue
                bullets.append(text)

            return {
                "headings": filter_headings(extract_headings(page)),
                "paragraphs": paragraphs,
                "bullet_lists": bullets,
            }
        finally:
            browser.close()


# ============================================================
# FEATURE EXTRACTION
# ============================================================
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
    if word_count < 1000:
        return 4
    return 5


def text_style(avg_len):
    if avg_len < 15:
        return "Concise"
    if avg_len < 35:
        return "Balanced"
    return "Detailed"


def information_complexity(word_count, heading_count):
    score = 1
    score += word_count > 300
    score += word_count > 600
    score += heading_count > 5
    return min(score, 5)


# ============================================================
# MAIN
# ============================================================
def extract_features(url):
    """Scrape a page and save one JSON document with all results."""
    data = scrape_page(url)

    headings = data["headings"]
    paragraphs = data["paragraphs"]
    bullets = data["bullet_lists"]
    word_count = count_words(paragraphs)
    heading_count = len(headings)
    paragraph_count = len(paragraphs)
    average_length = average_paragraph_length(paragraphs)

    features = {
        "url": url,
        "word_count": word_count,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "bullet_list_count": len(bullets),
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
            "bullet_lists": bullets,
        },
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print(f"\nSaved JSON → {OUTPUT_JSON}")

    return result


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    extract_features(URL)