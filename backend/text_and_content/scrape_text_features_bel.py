import json
import re

from playwright.sync_api import sync_playwright


URL = "https://www.belfius.be/site/professional/nl/producten/sparen-beleggen"
OUTPUT_JSON = "belfius_features.json"
WORD_PATTERN = re.compile(r"\w+")

HEADING_PATTERNS = (
    r"belfius", r"producten", r"professioneel", r"menu", r"contact",
    r"privacy", r"cookie", r"voorwaarden", r"help", r"jobs", r"social",
    r"volg ons", r"footer", r"navigatie", r"tarieven", r"documenten",
    r"pdf", r"tools", r"zoek", r"login", r"mybelfius", r"openingsuren",
    r"kantoren", r"faq", r"sparen-beleggen", r"andere websites",
    r"online bankieren", r"diensten", r"sectoren", r"een noodgeval",
)

COOKIE_PARAGRAPH_PATTERNS = (
    r"deze cookies", r"cookies", r"advertentie", r"socialmediacookies",
    r"veiligheid en de goede werking", r"voorkeuren te onthouden",
    r"hoeveel mensen onze websites bezoeken", r"gepersonaliseerde aanbevelingen",
)

BULLET_PATTERNS = (
    r"producten", r"spaar", r"beleggingsoplossingen",
    r"elektronische afschriften", r"coda", r"veiligheid",
    r"medische beroepen", r"juridische beroepen", r"meld een fraude",
    r"geef een schade aan", r"blokkeer een kaart", r"checkbox", r"label",
    r"belfius direct net", r"belfius mobile app",
)

def extract_headings(page):
    """Return all headings found through their ARIA role."""
    return page.get_by_role("heading").all_inner_texts()


def filter_real_headings(headings):
    """Keep meaningful headings and remove site navigation headings."""
    cleaned_headings = []

    for heading in headings:
        heading = heading.strip()
        if len(heading) < 8 or not re.search(r"[A-Za-z]", heading):
            continue
        if any(
            re.search(pattern, heading.lower())
            for pattern in HEADING_PATTERNS
        ):
            continue
        cleaned_headings.append(heading)

    return cleaned_headings


def scrape_page(url: str):
    """Load a page and extract the content used by the feature metrics."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(url, timeout=60_000)
            page.wait_for_timeout(2_000)

            paragraphs = [
                paragraph
                for paragraph in page.locator("p").all_inner_texts()
                if not any(
                    re.search(pattern, paragraph.lower())
                    for pattern in COOKIE_PARAGRAPH_PATTERNS
                )
            ]

            bullet_lists = []
            for bullet in page.locator("ul li, ol li").all_inner_texts():
                cleaned_bullet = bullet.strip()
                if len(cleaned_bullet) <= 5:
                    continue
                if any(
                    re.search(pattern, cleaned_bullet.lower())
                    for pattern in BULLET_PATTERNS
                ):
                    continue
                bullet_lists.append(cleaned_bullet)

            return {
                "title": page.title(),
                "headings": filter_real_headings(extract_headings(page)),
                "paragraphs": paragraphs,
                "bullet_lists": bullet_lists,
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
    """Scrape a page, calculate features, and save one complete JSON result."""
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
        "page_title": data["title"],
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
