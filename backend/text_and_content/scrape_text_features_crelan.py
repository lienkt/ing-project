
"""
Crelan Product Page Text Feature Scraper
=========================================

Target:
https://www.crelan.be/nl/particulieren/sparen-en-beleggen/sparen/product/spaarrekeningen

Extracted variables:

    word_count
    heading_count
    paragraph_count
    bullet_list_count
    average_paragraph_length
    headline_length
    text_density
    text_style
    information_complexity

Definitions
-----------

word_count:
    Number of visible words in the main product-page content.

heading_count:
    Number of visible headings.

paragraph_count:
    Number of visible body paragraphs.

bullet_list_count:
    Number of <ul> and <ol> lists.
    Individual bullets are NOT counted separately.

average_paragraph_length:
    Average number of words per visible body paragraph.

headline_length:
    Number of words in the main H1 headline.

text_density:
    Scale 1-5.
        1 = Very low
        5 = Very high

text_style:
    One of:
        Concise
        Balanced
        Detailed

information_complexity:
    Scale 1-5.
        1 = Very simple
        5 = Very complex

Important
---------

The visible text inside comparison tables is INCLUDED in word_count.

However:
    - table cells are NOT counted as paragraphs
    - table cells are NOT counted as bullet lists

The scraper removes:
    - navigation
    - footer
    - scripts
    - styles
    - forms
    - cookie UI
    - modal/overlay UI
    - hidden elements
    - social/share UI

Outputs
-------

scraped_output/
    crelan_spaarrekeningen_features.json
"""


# ============================================================
# IMPORTS
# ============================================================

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Dict, List

import requests
from bs4 import BeautifulSoup, Tag


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_URL = (
    "https://www.crelan.be/nl/particulieren/"
    "sparen-en-beleggen/sparen/product/spaarrekeningen"
)

DEFAULT_OUTPUT_DIR = Path("scraped_output")
OUTPUT_FILENAME = "crelan_spaarrekeningen_features.json"

REQUEST_TIMEOUT = 30

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/153.0.0.0 Safari/537.36"
)


# ============================================================
# HTML ELEMENTS TO REMOVE
# ============================================================

REMOVE_TAGS = [
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "nav",
    "footer",
    "form",
]


# IMPORTANT:
# Do not put "nav" here.
#
# "nav" is already handled by REMOVE_TAGS.
#
# Searching for "nav" as a substring inside classes can
# accidentally remove legitimate content.
#
REMOVE_CLASS_KEYWORDS = [
    "cookie",
    "consent",
    "privacy",
    "breadcrumb",
    "social",
    "share",
    "modal",
    "popup",
    "overlay",
]


# ============================================================
# HTTP DOWNLOAD
# ============================================================

def download_page(url: str) -> str:
    """
    Download webpage HTML.

    Returns
    -------
    str
        Raw HTML source.
    """

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "image/avif,"
            "image/webp,"
            "*/*;q=0.8"
        ),
        "Accept-Language": "nl-BE,nl;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    print("Downloading:")
    print(url)
    print()

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        print("ERROR: Could not download the webpage.")
        print()
        print(exc)
        sys.exit(1)

    print(f"HTTP status: {response.status_code}")
    print(f"Downloaded: {len(response.content):,} bytes")
    print()

    return response.text


# ============================================================
# BEAUTIFULSOUP SAFETY
# ============================================================

def is_valid_tag(tag) -> bool:
    """
    Safely check whether an object is a usable BeautifulSoup Tag.

    BeautifulSoup can sometimes leave decomposed tags with:

        tag.attrs = None

    Therefore this helper is used before accessing attributes.
    """

    return (
        isinstance(tag, Tag)
        and tag.attrs is not None
    )


# ============================================================
# HIDDEN ELEMENT DETECTION
# ============================================================

def is_hidden_element(tag: Tag) -> bool:
    """
    Determine whether an element is hidden.

    This function is deliberately defensive because BeautifulSoup
    may encounter tags whose attrs have already been decomposed.
    """

    if not isinstance(tag, Tag):
        return False

    # Critical safety check.
    if tag.attrs is None:
        return True

    # --------------------------------------------------------
    # HTML hidden attribute
    # --------------------------------------------------------

    if tag.has_attr("hidden"):
        return True

    # --------------------------------------------------------
    # aria-hidden
    # --------------------------------------------------------

    aria_hidden = tag.get("aria-hidden")

    if isinstance(aria_hidden, str):

        if aria_hidden.lower() == "true":
            return True

    # --------------------------------------------------------
    # Inline CSS
    # --------------------------------------------------------

    style = tag.get("style", "")

    if not isinstance(style, str):
        style = ""

    # Remove whitespace so all of these are detected:
    #
    # display:none
    # display: none
    #
    normalized_style = (
        style
        .lower()
        .replace(" ", "")
        .replace("\n", "")
        .replace("\t", "")
    )

    hidden_patterns = [
        "display:none",
        "visibility:hidden",
        "opacity:0",
    ]

    for pattern in hidden_patterns:

        if pattern in normalized_style:
            return True

    # --------------------------------------------------------
    # CSS classes
    # --------------------------------------------------------

    classes = tag.get("class", [])

    if isinstance(classes, list):

        classes_text = " ".join(
            str(item)
            for item in classes
        )

    else:

        classes_text = str(classes)

    classes_text = classes_text.lower()

    hidden_class_patterns = [
        "visually-hidden",
        "sr-only",
        "screen-reader",
        "screenreader",
    ]

    for pattern in hidden_class_patterns:

        if pattern in classes_text:
            return True

    return False


# ============================================================
# REMOVE UNWANTED ELEMENTS
# ============================================================

def remove_unwanted_elements(soup: BeautifulSoup) -> None:
    """
    Remove navigation, footer, scripts, cookie UI, etc.

    This implementation avoids the previous attrs=None error.

    Important:
    We first identify elements to remove and then decompose them.
    We do NOT modify the document while traversing soup.find_all().
    """

    # --------------------------------------------------------
    # STEP 1
    # Remove known HTML elements.
    # --------------------------------------------------------

    for tag_name in REMOVE_TAGS:

        elements = soup.find_all(tag_name)

        for element in elements:

            if not is_valid_tag(element):
                continue

            element.decompose()

    # --------------------------------------------------------
    # STEP 2
    # Find unwanted UI elements.
    # --------------------------------------------------------

    elements_to_remove = []

    for tag in soup.find_all(True):

        if not is_valid_tag(tag):
            continue

        # ----------------------------------------------------
        # Hidden element
        # ----------------------------------------------------

        if is_hidden_element(tag):

            elements_to_remove.append(tag)
            continue

        # ----------------------------------------------------
        # CSS classes
        # ----------------------------------------------------

        classes = tag.get("class", [])

        if isinstance(classes, list):

            classes_text = " ".join(
                str(item)
                for item in classes
            )

        else:

            classes_text = str(classes)

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        element_id = tag.get("id", "")

        if not isinstance(element_id, str):
            element_id = str(element_id)

        combined = (
            f"{classes_text} {element_id}"
        ).lower()

        # ----------------------------------------------------
        # Determine whether this is unwanted UI
        # ----------------------------------------------------

        should_remove = False

        for keyword in REMOVE_CLASS_KEYWORDS:

            if keyword in combined:

                should_remove = True
                break

        if should_remove:

            elements_to_remove.append(tag)

    # --------------------------------------------------------
    # STEP 3
    # Decompose AFTER traversal.
    # --------------------------------------------------------

    for tag in elements_to_remove:

        if not isinstance(tag, Tag):
            continue

        if tag.attrs is None:
            continue

        try:
            tag.decompose()
        except Exception:
            # Element may already have been removed as a child
            # of another decomposed element.
            pass


# ============================================================
# FIND MAIN CONTENT
# ============================================================

def find_main_content(soup: BeautifulSoup) -> Tag:
    """
    Find the main product-page content.

    Priority:

        1. <main>
        2. <article>
        3. common content containers
        4. <body>
    """

    # --------------------------------------------------------
    # <main>
    # --------------------------------------------------------

    main = soup.find("main")

    if is_valid_tag(main):
        return main

    # --------------------------------------------------------
    # <article>
    # --------------------------------------------------------

    article = soup.find("article")

    if is_valid_tag(article):
        return article

    # --------------------------------------------------------
    # Common content selectors
    # --------------------------------------------------------

    selectors = [
        "#main-content",
        "#content",
        ".main-content",
        ".region-content",
        ".content",
    ]

    for selector in selectors:

        element = soup.select_one(selector)

        if is_valid_tag(element):
            return element

    # --------------------------------------------------------
    # <body>
    # --------------------------------------------------------

    body = soup.find("body")

    if not is_valid_tag(body):

        raise RuntimeError(
            "Could not find main content or <body>."
        )

    return body


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace.
    """

    if not text:
        return ""

    # Replace non-breaking spaces.
    text = text.replace("\xa0", " ")

    # Normalize whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def clean_text(text: str) -> str:
    """
    Clean extracted text.
    """

    return normalize_whitespace(text)


# ============================================================
# WORD TOKENIZATION
# ============================================================

def tokenize_words(text: str) -> List[str]:
    """
    Tokenize visible text into words.

    Designed for Dutch financial webpages.

    Examples recognized as words/tokens:

        Crelan
        spaarrekening
        gereglementeerde
        rekening-houder
        500.000
        1,50
        rente
    """

    if not text:
        return []

    pattern = (
        r"\b"
        r"[\wÀ-ÖØ-öø-ÿ]+"
        r"(?:[-'][\wÀ-ÖØ-öø-ÿ]+)*"
        r"\b"
    )

    return re.findall(
        pattern,
        text,
        flags=re.UNICODE,
    )


def count_words(text: str) -> int:
    """
    Count words in text.
    """

    return len(
        tokenize_words(text)
    )


# ============================================================
# EXTRACT HEADINGS
# ============================================================

def extract_headings(main: Tag) -> List[str]:
    """
    Extract visible H1-H6 headings.
    """

    headings = []

    for tag in main.find_all(
        ["h1", "h2", "h3", "h4", "h5", "h6"]
    ):

        if not is_valid_tag(tag):
            continue

        if is_hidden_element(tag):
            continue

        text = clean_text(
            tag.get_text(
                " ",
                strip=True,
            )
        )

        if text:

            headings.append(text)

    return headings


# ============================================================
# EXTRACT PARAGRAPHS
# ============================================================

def extract_paragraphs(main: Tag) -> List[str]:
    """
    Extract visible body paragraphs.

    Paragraphs inside tables are excluded.

    Paragraphs that are empty after cleaning are excluded.
    """

    paragraphs = []

    for p in main.find_all("p"):

        if not is_valid_tag(p):
            continue

        if is_hidden_element(p):
            continue

        # ----------------------------------------------------
        # Do not count table paragraphs as normal paragraphs.
        # ----------------------------------------------------

        if p.find_parent("table") is not None:
            continue

        text = clean_text(
            p.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        paragraphs.append(text)

    return paragraphs


# ============================================================
# EXTRACT BULLET / NUMBERED LISTS
# ============================================================

def extract_lists(main: Tag) -> List[str]:
    """
    Extract visible unordered and ordered lists.

    One <ul> or <ol> = one list.

    Individual <li> elements are NOT counted separately.
    """

    lists = []

    for list_tag in main.find_all(
        ["ul", "ol"]
    ):

        if not is_valid_tag(list_tag):
            continue

        if is_hidden_element(list_tag):
            continue

        text = clean_text(
            list_tag.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        lists.append(text)

    return lists


# ============================================================
# EXTRACT TABLES
# ============================================================

def extract_tables(main: Tag) -> List[str]:
    """
    Extract visible table text.

    Table text is included in word_count.

    Tables themselves are not counted as paragraphs.
    """

    tables = []

    for table in main.find_all("table"):

        if not is_valid_tag(table):
            continue

        if is_hidden_element(table):
            continue

        text = clean_text(
            table.get_text(
                " ",
                strip=True,
            )
        )

        if not text:
            continue

        tables.append(text)

    return tables


# ============================================================
# EXTRACT ALL VISIBLE MAIN CONTENT TEXT
# ============================================================

def extract_visible_text(main: Tag) -> str:
    """
    Extract visible text from the main product content.

    Includes:

        - headings
        - paragraphs
        - lists
        - comparison tables
        - table cells
        - other visible content

    Excludes:

        - script
        - style
        - hidden content
        - navigation
        - footer
        - removed UI
    """

    text_parts = []

    for text_node in main.find_all(
        string=True
    ):

        parent = text_node.parent

        if parent is None:
            continue

        if not isinstance(parent, Tag):
            continue

        if parent.attrs is None:
            continue

        # ----------------------------------------------------
        # Ignore hidden elements.
        # ----------------------------------------------------

        if is_hidden_element(parent):
            continue

        # ----------------------------------------------------
        # Ignore non-content tags.
        # ----------------------------------------------------

        if parent.name in REMOVE_TAGS:
            continue

        # ----------------------------------------------------
        # Extract text.
        # ----------------------------------------------------

        text = str(text_node).strip()

        if not text:
            continue

        text_parts.append(text)

    combined_text = " ".join(
        text_parts
    )

    return clean_text(
        combined_text
    )


# ============================================================
# FIND MAIN HEADLINE
# ============================================================

def find_main_headline(
    main: Tag,
    headings: List[str],
) -> str:
    """
    Find primary page headline.

    Priority:

        1. H1
        2. first visible heading
        3. empty string
    """

    h1 = main.find("h1")

    if is_valid_tag(h1):

        text = clean_text(
            h1.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            return text

    if headings:
        return headings[0]

    return ""


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_sentences(text: str) -> List[str]:
    """
    Basic sentence segmentation.

    This is used only for information-complexity estimation.
    """

    text = clean_text(text)

    if not text:
        return []

    # --------------------------------------------------------
    # Protect decimal numbers.
    #
    # Example:
    #
    # 1.50
    #
    # should not become two sentences.
    # --------------------------------------------------------

    protected = re.sub(
        r"(\d)\.(\d)",
        r"\1<DECIMAL>\2",
        text,
    )

    # --------------------------------------------------------
    # Protect a few common abbreviations.
    # --------------------------------------------------------

    abbreviations = [
        "dhr.",
        "mevr.",
        "bv.",
        "etc.",
        "m.b.t.",
    ]

    for abbreviation in abbreviations:

        replacement = (
            abbreviation
            .replace(".", "<DOT>")
        )

        protected = protected.replace(
            abbreviation,
            replacement,
        )

    # --------------------------------------------------------
    # Split sentences.
    # --------------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+",
        protected,
    )

    restored = []

    for sentence in sentences:

        sentence = (
            sentence
            .replace("<DECIMAL>", ".")
            .replace("<DOT>", ".")
        )

        sentence = clean_text(
            sentence
        )

        if sentence:
            restored.append(sentence)

    return restored


# ============================================================
# TEXT DENSITY
# ============================================================

def calculate_text_density(
    word_count: int,
    heading_count: int,
    paragraph_count: int,
    bullet_list_count: int,
) -> int:
    """
    Calculate text density on a 1-5 scale.

        1 = Very low
        2 = Low
        3 = Medium
        4 = High
        5 = Very high

    The score is based on:

        - total amount of text
        - average words per paragraph
        - content-block density
    """

    if word_count <= 0:
        return 1

    # --------------------------------------------------------
    # Average words per paragraph.
    # --------------------------------------------------------

    if paragraph_count > 0:

        average_paragraph_length = (
            word_count / paragraph_count
        )

    else:

        average_paragraph_length = word_count

    # --------------------------------------------------------
    # Number of structural blocks.
    # --------------------------------------------------------

    content_blocks = (
        heading_count
        + paragraph_count
        + bullet_list_count
    )

    if content_blocks > 0:

        words_per_block = (
            word_count / content_blocks
        )

    else:

        words_per_block = word_count

    # --------------------------------------------------------
    # Base score from total word count.
    # --------------------------------------------------------

    if word_count < 150:

        score = 1

    elif word_count < 350:

        score = 2

    elif word_count < 700:

        score = 3

    elif word_count < 1200:

        score = 4

    else:

        score = 5

    # --------------------------------------------------------
    # Long paragraphs indicate higher density.
    # --------------------------------------------------------

    if average_paragraph_length > 60:
        score += 1

    # --------------------------------------------------------
    # High words per structural block indicate density.
    # --------------------------------------------------------

    if words_per_block > 45:
        score += 1

    # --------------------------------------------------------
    # Keep within 1-5.
    # --------------------------------------------------------

    score = max(
        1,
        min(5, score),
    )

    return score


# ============================================================
# TEXT STYLE
# ============================================================

def classify_text_style(
    word_count: int,
    average_paragraph_length: float,
) -> str:
    """
    Classify text style.

    Allowed values:

        Concise
        Balanced
        Detailed
    """

    if word_count <= 0:
        return "Concise"

    # --------------------------------------------------------
    # Concise
    # --------------------------------------------------------

    if (
        word_count <= 350
        and average_paragraph_length <= 25
    ):
        return "Concise"

    # --------------------------------------------------------
    # Detailed
    # --------------------------------------------------------

    if (
        word_count >= 1000
        or average_paragraph_length >= 50
    ):
        return "Detailed"

    # --------------------------------------------------------
    # Everything else.
    # --------------------------------------------------------

    return "Balanced"


# ============================================================
# INFORMATION COMPLEXITY
# ============================================================

def calculate_information_complexity(
    full_text: str,
    paragraphs: List[str],
) -> int:
    """
    Estimate information complexity on a 1-5 scale.

        1 = Very simple
        2 = Simple
        3 = Moderate
        4 = Complex
        5 = Very complex

    Factors:

        - sentence length
        - long-word ratio
        - numeric content
        - financial terminology
        - paragraph length

    This is a deterministic heuristic.
    """

    if not full_text:
        return 1

    words = tokenize_words(
        full_text
    )

    if not words:
        return 1

    # --------------------------------------------------------
    # SENTENCE LENGTH
    # --------------------------------------------------------

    sentences = split_sentences(
        full_text
    )

    sentence_lengths = []

    for sentence in sentences:

        sentence_words = tokenize_words(
            sentence
        )

        if sentence_words:

            sentence_lengths.append(
                len(sentence_words)
            )

    if sentence_lengths:

        average_sentence_length = (
            statistics.mean(
                sentence_lengths
            )
        )

    else:

        average_sentence_length = len(words)

    # --------------------------------------------------------
    # LONG WORD RATIO
    # --------------------------------------------------------

    long_words = [
        word
        for word in words
        if len(word) >= 10
    ]

    long_word_ratio = (
        len(long_words)
        / max(len(words), 1)
    )

    # --------------------------------------------------------
    # NUMERIC CONTENT
    # --------------------------------------------------------

    numeric_tokens = [
        word
        for word in words
        if re.search(
            r"\d",
            word,
        )
    ]

    numeric_ratio = (
        len(numeric_tokens)
        / max(len(words), 1)
    )

    # --------------------------------------------------------
    # FINANCIAL / BANKING TERMS
    # --------------------------------------------------------

    financial_terms = [
        "rente",
        "basisrente",
        "getrouwheidspremie",
        "spaarrekening",
        "spaarrekeningen",
        "interest",
        "intrest",
        "fiscaliteit",
        "roerende",
        "voorheffing",
        "depositogarantiestelsel",
        "faillissement",
        "inflatierisico",
        "gereglementeerd",
        "gereglementeerde",
        "voorwaarden",
        "maximuminlage",
        "rekeninghouder",
        "rekeninghouders",
        "medetitularis",
        "titularis",
        "creditverrichtingen",
        "debetsaldo",
        "aanslagjaar",
        "belastingaangifte",
        "bail-in",
        "belasting",
        "spaartegoed",
        "getrouwheid",
        "kapitaal",
        "vergoeding",
        "rentevoet",
        "rentevoeten",
    ]

    lower_text = full_text.lower()

    financial_term_count = 0

    for term in financial_terms:

        financial_term_count += (
            lower_text.count(term)
        )

    financial_density = (
        financial_term_count
        / max(len(words), 1)
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = 1

    # --------------------------------------------------------
    # Sentence complexity.
    # --------------------------------------------------------

    if average_sentence_length >= 12:
        score += 1

    if average_sentence_length >= 20:
        score += 1

    if average_sentence_length >= 30:
        score += 1

    # --------------------------------------------------------
    # Long words.
    # --------------------------------------------------------

    if long_word_ratio >= 0.10:
        score += 1

    if long_word_ratio >= 0.18:
        score += 1

    # --------------------------------------------------------
    # Numeric / financial information.
    # --------------------------------------------------------

    if numeric_ratio >= 0.02:
        score += 1

    if financial_density >= 0.005:
        score += 1

    # --------------------------------------------------------
    # Paragraph length.
    # --------------------------------------------------------

    paragraph_lengths = []

    for paragraph in paragraphs:

        paragraph_words = tokenize_words(
            paragraph
        )

        if paragraph_words:

            paragraph_lengths.append(
                len(paragraph_words)
            )

    if paragraph_lengths:

        average_paragraph_length = (
            statistics.mean(
                paragraph_lengths
            )
        )

        if average_paragraph_length >= 40:
            score += 1

        if average_paragraph_length >= 70:
            score += 1

    # --------------------------------------------------------
    # Keep 1-5.
    # --------------------------------------------------------

    score = max(
        1,
        min(5, score),
    )

    return score


# ============================================================
# EXTRACT ALL FEATURES
# ============================================================

def extract_features(html: str, url: str) -> Dict:
    """Extract calculated features and their source results from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    remove_unwanted_elements(soup)
    main = find_main_content(soup)

    headings = extract_headings(main)
    paragraphs = extract_paragraphs(main)
    lists = extract_lists(main)
    tables = extract_tables(main)
    full_text = extract_visible_text(main)
    headline = find_main_headline(main, headings)

    word_count = count_words(full_text)
    heading_count = len(headings)
    paragraph_count = len(paragraphs)
    bullet_list_count = len(lists)
    paragraph_lengths = [count_words(text) for text in paragraphs]
    average_paragraph_length = round(
        statistics.mean(paragraph_lengths), 2
    ) if paragraph_lengths else 0.0

    return {
        "url": url,
        "word_count": word_count,
        "heading_count": heading_count,
        "paragraph_count": paragraph_count,
        "bullet_list_count": bullet_list_count,
        "average_paragraph_length": average_paragraph_length,
        "headline_length": count_words(headline),
        "text_density": calculate_text_density(
            word_count, heading_count, paragraph_count, bullet_list_count
        ),
        "text_style": classify_text_style(
            word_count, average_paragraph_length
        ),
        "information_complexity": calculate_information_complexity(
            full_text, paragraphs
        ),
        "table_count": len(tables),
        "table_word_count": sum(count_words(table) for table in tables),
        "source": {
            "headline": headline,
            "headings": headings,
            "paragraphs": paragraphs,
            "lists": lists,
            "tables": tables,
            "full_text": full_text,
        },
    }


def save_json(
    features: Dict,
    output_dir: Path,
) -> Path:
    """
    Save all features to JSON.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_dir / OUTPUT_FILENAME

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            features,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return output_file


# ============================================================
# ARGUMENT PARSER
# ============================================================

def parse_arguments():
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Scrape text features from a Crelan "
            "product webpage."
        )
    )

    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=(
            "URL to scrape. "
            "Defaults to the Crelan savings-account page."
        ),
    )

    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=(
            "Output directory. "
            "Defaults to scraped_output."
        ),
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():
    """
    Main execution function.
    """

    args = parse_arguments()

    url = args.url

    output_dir = Path(
        args.output_dir
    )

    html = download_page(url)

    try:
        features = extract_features(html=html, url=url)

    except Exception as exc:
        print(f"ERROR: Extraction failed: {type(exc).__name__}: {exc}")
        raise

    output_file = save_json(features, output_dir)
    print(f"Saved JSON: {output_file}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()