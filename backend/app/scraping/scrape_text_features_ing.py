from playwright.sync_api import sync_playwright
import re
import json

# -----------------------------
# Extract headings using ARIA roles
# -----------------------------
def extract_headings(page):
    return page.get_by_role("heading").all_inner_texts()


# -----------------------------
# CLEAN HEADINGS: exclude ONLY unrealistic ones
# -----------------------------
def filter_real_headings(headings):

    remove_patterns = [
        r"our products", r"ing belgium", r"our website", r"follow us",
        r"looking for", r"join thousands", r"financial independence",
        r"get ready", r"apply online", r"look out", r"cookie", r"privacy",
        r"terms", r"manage", r"need to", r"itsme", r"cash dispenser",
        r"savings account", r"ing save up",

        r"go to 18", r"is a youth account really free", r"can i open",
        r"who is the holder", r"how can i access", r"what level of control",
        r"does my child receive", r"carry your bank", r"replacement bank card",

        r"what happens if the debit card is lost or stolen",
        r"what happens when my child turns 18",
        r"also interesting",
    ]

    cleaned = []
    for h in headings:
        h_clean = h.strip()
        h_lower = h_clean.lower()

        if any(re.search(pattern, h_lower) for pattern in remove_patterns):
            continue

        cleaned.append(h_clean)

    return cleaned


# -----------------------------
# SCRAPER
# -----------------------------
def scrape_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(2000)

        headings = extract_headings(page)
        headings = filter_real_headings(headings)

        paragraphs = page.locator("p").all_inner_texts()
        bullet_lists = page.locator("ul li, ol li").all_inner_texts()

        browser.close()

        return {
            "headings": headings,
            "paragraphs": paragraphs,
            "bullet_lists": bullet_lists
        }


# -----------------------------
# FEATURE EXTRACTION
# -----------------------------
def count_words(text_list):
    return sum(len(re.findall(r"\w+", t)) for t in text_list)

def average_paragraph_length(paragraphs):
    if len(paragraphs) == 0:
        return 0
    return count_words(paragraphs) / len(paragraphs)

def headline_length(headings):
    if len(headings) == 0:
        return 0
    return len(re.findall(r"\w+", headings[0]))

def text_density(word_count):
    if word_count < 150: return 1
    elif word_count < 300: return 2
    elif word_count < 600: return 3
    elif word_count < 1000: return 4
    else: return 5

def text_style(avg_len):
    if avg_len < 15: return "Concise"
    elif avg_len < 35: return "Balanced"
    else: return "Detailed"

def information_complexity(word_count, heading_count):
    score = 1
    if word_count > 300: score += 1
    if word_count > 600: score += 1
    if heading_count > 5: score += 1
    return min(score, 5)


# -----------------------------
# MAIN — ONLY RETURN 9 METRICS
# -----------------------------
def extract_features(url):
    data = scrape_page(url)

    word_count = count_words(data["paragraphs"])
    heading_count = len(data["headings"])
    paragraph_count = len(data["paragraphs"])
    bullet_list_count = len(data["bullet_lists"])
    avg_paragraph_len = average_paragraph_length(data["paragraphs"])
    headline_len = headline_length(data["headings"])
    density = text_density(word_count)
    style = text_style(avg_paragraph_len)
    complexity = information_complexity(word_count, heading_count)

    features = {
        "word_count": word_count,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "bullet_list_count": bullet_list_count,
        "average_paragraph_length": avg_paragraph_len,
        "headline_length": headline_len,
        "text_density": density,
        "text_style": style,
        "information_complexity": complexity
    }

    # Save JSON
    with open("ing_youth_account_features.json", "w", encoding="utf-8") as f:
        json.dump(features, f, indent=4, ensure_ascii=False)

    print("Saved JSON → ing_youth_account_features.json")
    return features


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    url = "https://www.ing.be/en/individuals/current-accounts-packs/youth-account"
    extract_features(url)
