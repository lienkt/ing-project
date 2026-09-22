"""Extract and rank calls to action from rendered product pages."""

import re
import unicodedata
from collections import Counter
from typing import Any, TypedDict

from playwright.async_api import Page

import cta_config as config


class CtaCandidate(TypedDict):
    """Rendered information used to assess a possible CTA."""

    text: str
    href: str | None
    classes: str
    y: float
    area: float
    background: str
    font_size: float
    font_weight: int


# Text normalization and CTA classification

def clean_text(value: str) -> str:
    """Collapse whitespace and trim a text value."""
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_text(value: str) -> str:
    """Normalize text for case- and accent-insensitive matching."""
    text = clean_text(value).casefold().replace("’", "'").replace("`", "'")
    text = unicodedata.normalize("NFKD", text)
    return "".join(character for character in text if not unicodedata.combining(character))


def normalize_input_url(raw: str) -> str:
    """Accept a URL or an HTML anchor containing an ``href`` attribute."""
    match = re.search(r'href=["\']([^"\']+)', clean_text(raw), re.IGNORECASE)
    return match.group(1) if match else clean_text(raw)


def _contains_phrase(text: str, phrase: str) -> bool:
    phrase = normalize_text(phrase)
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return bool(phrase and re.search(pattern, normalize_text(text)))


def classify_cta_type(text: str) -> str:
    """Return the category with the most specific matching phrase."""
    matches = [
        (len(normalize_text(word)), category)
        for category, words in config.CTA_TYPE_KEYWORDS.items()
        for word in words
        if _contains_phrase(text, word)
    ]
    return max(matches, default=(0, "Other"))[1]


def _has_cta_class(classes: str) -> bool:
    classes = normalize_text(classes)
    return any(normalize_text(marker) in classes for marker in config.CTA_CLASS_MARKERS)


def _looks_like_cta(text: str, tag: str, role: str, classes: str) -> bool:
    text = clean_text(text)
    if not text or len(text) > 180:
        return False
    if _is_excluded(text):
        return False
    keyword_match = any(_contains_phrase(text, word) for word in config.CTA_KEYWORDS)
    semantic_button = tag.casefold() in {"button", "input"} or role.casefold() == "button"
    return keyword_match or _has_cta_class(classes) or (semantic_button and len(text) >= 2)


def _is_excluded(text: str) -> bool:
    """Return whether text belongs to cookies, navigation, or legal content."""
    normalized_text = normalize_text(text)
    return any(
        normalize_text(excluded) in normalized_text
        for excluded in config.EXCLUDE_TEXT
    )


# Candidate collection
async def _collect_candidates(page: Page) -> list[CtaCandidate]:
    """Collect visible CTA candidates outside layout navigation regions."""
    candidates: list[CtaCandidate] = []
    elements = page.locator(config.CTA_SELECTOR)
    style_script = """
    element => {
      const style = getComputedStyle(element);
      return {
        background: style.backgroundColor,
        fontSize: parseFloat(style.fontSize) || 0,
        fontWeight: parseInt(style.fontWeight) || 400,
      };
    }
    """
    for index in range(await elements.count()):
        element = elements.nth(index)
        try:
            in_layout_area = await element.evaluate(
                "element => Boolean(element.closest('header, nav, footer'))"
            )
            if not await element.is_visible() or in_layout_area:
                continue
            text = clean_text(await element.inner_text(timeout=1_200))
            if not text:
                value = await element.get_attribute("value")
                aria_label = await element.get_attribute("aria-label")
                text = clean_text(value or aria_label or "")
            tag = await element.evaluate("e => e.tagName.toLowerCase()")
            role = await element.get_attribute("role") or ""
            classes = await element.get_attribute("class") or ""
            if not _looks_like_cta(text, tag, role, classes):
                continue
            box = await element.bounding_box()
            if not box:
                continue
            style = await element.evaluate(style_script)
            scroll_y = await page.evaluate("window.scrollY")
            candidates.append(
                {
                    "text": text,
                    "href": await element.get_attribute("href"),
                    "classes": classes,
                    "y": round(box["y"] + scroll_y, 1),
                    "area": round(box["width"] * box["height"], 1),
                    "background": style["background"],
                    "font_size": style["fontSize"],
                    "font_weight": style["fontWeight"],
                }
            )
        except Exception:
            continue
    return candidates


# CTA ranking and feature output
def _prominence_score(item: CtaCandidate, viewport_height: int) -> int:
    score = 1 + (item["y"] < viewport_height) + (item["area"] >= 6_000)
    score += item["font_weight"] >= 600 or item["font_size"] >= 18
    score += item["background"] not in {"", "transparent", "rgba(0, 0, 0, 0)"}
    return min(5, int(score))


def _select_primary(
    items: list[CtaCandidate], viewport_height: int
) -> CtaCandidate | None:
    return max(
        items,
        key=lambda item: (
            classify_cta_type(item["text"]) != "Other",
            _prominence_score(item, viewport_height),
            item["y"] < viewport_height,
            item["area"],
            -item["y"],
        ),
        default=None,
    )


async def extract_cta_features(page: Page, url: str) -> dict[str, Any]:
    """Load ``url`` and return CTA metrics for its rendered page."""
    await page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=config.PAGE_TIMEOUT_MS,
    )
    try:
        await page.wait_for_load_state("networkidle", timeout=config.NETWORK_IDLE_TIMEOUT_MS)
    except Exception:
        pass
    scroll_script = """async ({ steps, pause }) => {
        for (let index = 0; index < steps; index += 1) {
            const previousPosition = scrollY;
            scrollBy(0, Math.max(500, innerHeight * 0.8));
            await new Promise(done => setTimeout(done, pause));
            if (scrollY === previousPosition) break;
        }
        scrollTo(0, 0);
    }"""
    await page.evaluate(
        scroll_script,
        {"steps": config.MAX_SCROLL_STEPS, "pause": config.SCROLL_PAUSE_MS},
    )
    unique_candidates: list[CtaCandidate] = []
    seen_candidates: set[tuple[str, str, int]] = set()
    for item in await _collect_candidates(page):
        key = (
            normalize_text(item["text"]),
            item["href"] or "",
            round(item["y"] / 15),
        )
        if key not in seen_candidates:
            seen_candidates.add(key)
            unique_candidates.append(item)

    viewport_height = config.VIEWPORT["height"]
    primary = _select_primary(unique_candidates, viewport_height)
    text_counts = Counter(
        normalize_text(item["text"]) for item in unique_candidates
    )
    result = {
        "cta_count": len(unique_candidates),
        "primary_cta_text": primary["text"] if primary else None,
        "cta_above_fold": bool(primary and primary["y"] < viewport_height),
        "cta_repeated": bool(
            primary and text_counts[normalize_text(primary["text"])] > 1
        ),
        "cta_prominence": _prominence_score(primary, viewport_height)
        if primary
        else 1,
        "cta_type": classify_cta_type(primary["text"]) if primary else "Other",
    }
    if config.DEBUG_DETECTED_CTAS:
        result["detected_ctas"] = [
            {
                "text": item["text"],
                "type": classify_cta_type(item["text"]),
                "above_fold": item["y"] < viewport_height,
                "prominence": _prominence_score(item, viewport_height),
            }
            for item in unique_candidates
        ]
    return result
