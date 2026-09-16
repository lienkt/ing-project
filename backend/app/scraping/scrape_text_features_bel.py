from playwright.sync_api import sync_playwright
import re
import json

# -----------------------------
# Extract headings using ARIA roles
# -----------------------------
def extract_headings(page):
    return page.get_by_role("heading").all_inner_texts()


# -----------------------------
# CLEAN HEADINGS: dynamic filtering
# -----------------------------
def filter_real_headings(headings):

    remove_patterns = [
        r"belfius", r"producten", r"professioneel", r"menu", r"contact",
        r"privacy", r"cookie", r"voorwaarden", r"help", r"jobs", r"social",
        r"volg ons", r"footer", r"navigatie", r"tarieven", r"documenten",
        r"pdf", r"tools", r"zoek", r"login", r"mybelfius", r"openingsuren",
        r"kantoren", r"faq", r"sparen-beleggen",
        r"andere websites", r"online bankieren", r"diensten",
        r"sectoren", r"een noodgeval",
    ]

    cleaned = []
    for h in headings:
        h_clean = h.strip()
        h_lower = h_clean.lower()

        if any(re.search(pattern, h_lower) for pattern in remove_patterns):
            continue

        if len(h_clean) >= 8 and re.search(r"[A-Za-z]", h_clean):
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

        title = page.title()

        headings = extract_headings(page)
        headings = filter_real_headings(headings)

        paragraphs = page.locator("p").all_inner_texts()

        cookie_patterns = [
            r"deze cookies", r"cookies", r"advertentie", r"socialmediacookies",
            r"veiligheid en de goede werking", r"voorkeuren te onthouden",
            r"hoeveel mensen onze websites bezoeken",
            r"gepersonaliseerde aanbevelingen",
        ]

        clean_paragraphs = []
        for p_text in paragraphs:
            p_lower = p_text.lower()
            if any(re.search(pattern, p_lower) for pattern in cookie_patterns):
                continue
            clean_paragraphs.append(p_text)

        paragraphs = clean_paragraphs

        raw_bullets = page.locator("ul li, ol li").all_inner_texts()

        exclude_bullets = [
            r"producten", r"spaar", r"beleggingsoplossingen",
            r"elektronische afschriften", r"coda", r"veiligheid",
            r"medische beroepen", r"juridische beroepen",
            r"meld een fraude", r"geef een schade aan",
            r"blokkeer een kaart", r"checkbox", r"label",
            r"belfius direct net", r"belfius mobile app",
        ]

        bullet_lists = []
        for b in raw_bullets:
            text = b.strip().lower()
            if any(re.search(pattern, text) for pattern in exclude_bullets):
                continue
            if len(text) > 5:
                bullet_lists.append(b.strip())

        browser.close()

        return {
            "title": title,
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
# MAIN — ONLY RETURN 9 METRICS + SAVE JSON
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
    with open("belfius_features.json", "w", encoding="utf-8") as f:
        json.dump(features, f, indent=4, ensure_ascii=False)

    print("Saved JSON → belfius_features.json")
    return features


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    url = "https://www.belfius.be/site/professional/nl/producten/sparen-beleggen"
    extract_features(url)
