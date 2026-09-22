"""Text scoring rules used by the ING label extractor."""

import re
from collections.abc import Iterable


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


def calculate_text_style(
    word_count: int, average_paragraph_length: float, heading_count: int
) -> str:
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

    euro_count = len(
        re.findall(
            r"(?:€\s*[\d.,]+|[\d.,]+\s*€|EUR\s*[\d.,]+|[\d.,]+\s*EUR)",
            text,
            re.IGNORECASE,
        )
    )
    if euro_count >= 3:
        score += 1

    return min(score, 5)
