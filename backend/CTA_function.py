"""
Multilingual CTA extraction functions.

Supports:
- English
- French
- Dutch

The module extracts CTA candidates from rendered web pages,
classifies their intent, evaluates visual prominence and
selects the most likely primary CTA.
"""

import re
import unicodedata

from collections import Counter
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

import CTA_config as config


# ============================================================
# TEXT UTILITIES
# ============================================================

def clean_text(value: str) -> str:
    """
    Normalize whitespace and remove leading/trailing spaces.
    """
    return re.sub(r"\s+", " ", (value or "")).strip()


def normalize_text(value: str) -> str:
    """
    Normalize text for multilingual CTA matching.

    Operations:
    - lowercase
    - normalize apostrophes
    - remove accents
    - normalize whitespace
    """

    value = clean_text(value)

    value = (
        value
        .casefold()
        .replace("’", "'")
        .replace("`", "'")
    )

    value = unicodedata.normalize("NFKD", value)

    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    return value


def normalize_input_url(raw: str) -> str:
    """
    Accept either:
    - a plain URL
    - an HTML anchor string containing href="..."
    """

    raw = clean_text(raw)

    match = re.search(
        r'href=["\']([^"\']+)',
        raw,
        flags=re.IGNORECASE,
    )

    return match.group(1) if match else raw


# ============================================================
# CTA MATCHING
# ============================================================

def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Check whether a phrase occurs in normalized text.

    Short phrases use word boundaries to avoid accidental
    partial matches.
    """

    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    if not normalized_phrase:
        return False

    if len(normalized_phrase) <= 4:
        pattern = r"\b" + re.escape(normalized_phrase) + r"\b"
        return bool(re.search(pattern, normalized_text))

    return normalized_phrase in normalized_text


def classify_cta_type(text: str) -> str:
    """
    Classify CTA according to the configured CTA categories.

    The longest matching keyword wins. This means that a
    specific phrase such as:

        "calculate your insurance"

    takes priority over a generic match such as:

        "calculate"
    """

    matches = []

    for cta_type, keywords in config.CTA_TYPE_KEYWORDS.items():

        for keyword in keywords:

            if _contains_phrase(text, keyword):

                matches.append(
                    (
                        len(normalize_text(keyword)),
                        cta_type,
                    )
                )

    if not matches:
        return "Other"

    matches.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return matches[0][1]


def _is_excluded(text: str) -> bool:
    """
    Determine whether text belongs to navigation, cookies,
    legal content or another excluded category.
    """

    normalized = normalize_text(text)

    return any(
        normalize_text(excluded) in normalized
        for excluded in config.EXCLUDE_TEXT
    )


def _has_cta_class(classes: str) -> bool:
    """
    Check whether an element has a CTA-like CSS class.
    """

    normalized_classes = normalize_text(classes)

    return any(
        normalize_text(marker) in normalized_classes
        for marker in config.CTA_CLASS_MARKERS
    )


def _looks_like_cta(
    text: str,
    tag: str,
    role: str,
    classes: str,
) -> bool:
    """
    Determine whether an element is likely to be a CTA.

    A candidate is accepted when:
    - it has useful text
    - it is not excluded
    - it contains a known CTA phrase
      OR
    - it has a CTA-like CSS class
      OR
    - it is a button / role=button with meaningful text
    """

    text = clean_text(text)

    if not text:
        return False

    # Allow longer CTAs because some bank CTAs contain
    # contextual information.
    if len(text) > 180:
        return False

    if _is_excluded(text):
        return False

    keyword_hit = any(
        _contains_phrase(text, keyword)
        for keyword in config.CTA_KEYWORDS
    )

    class_hint = _has_cta_class(classes)

    tag = (tag or "").casefold()
    role = (role or "").casefold()

    semantic_button = (
        tag == "button"
        or role == "button"
        or tag in {"input"}
    )

    # A real button with meaningful text can be a CTA even if
    # its wording is not in the keyword dictionary.
    if semantic_button and len(text) >= 2:
        return True

    return keyword_hit or class_hint


# ============================================================
# CANDIDATE COLLECTION
# ============================================================

async def _collect_candidates(
    page: Page,
) -> List[Dict[str, Any]]:
    """
    Collect visible CTA candidates from the rendered page.
    """

    elements = page.locator(config.CTA_SELECTOR)

    total = await elements.count()

    candidates: List[Dict[str, Any]] = []

    style_js = """
    e => {
        const s = getComputedStyle(e);

        return {
            bg: s.backgroundColor || "",
            color: s.color || "",
            fontSize: parseFloat(s.fontSize) || 0,
            fontWeight: parseInt(s.fontWeight) || 400,
            borderRadius: parseFloat(s.borderRadius) || 0,
            display: s.display || "",
            visibility: s.visibility || "",
            opacity: parseFloat(s.opacity) || 1
        };
    }
    """

    for i in range(total):

        element = elements.nth(i)

        try:

            if not await element.is_visible():
                continue

            text = ""

            try:
                text = clean_text(
                    await element.inner_text(
                        timeout=1200
                    )
                )
            except Exception:
                pass

            # Fallback for input/button elements.
            if not text:

                value = await element.get_attribute("value")
                aria_label = await element.get_attribute(
                    "aria-label"
                )

                text = clean_text(
                    value
                    or aria_label
                    or ""
                )

            if not text:
                continue

            tag = await element.evaluate(
                "e => e.tagName.toLowerCase()"
            )

            role = (
                await element.get_attribute("role")
                or ""
            )

            classes = (
                await element.get_attribute("class")
                or ""
            )

            if not _looks_like_cta(
                text,
                tag,
                role,
                classes,
            ):
                continue

            box = await element.bounding_box()

            if not box:
                continue

            styles = await element.evaluate(
                style_js
            )

            scroll_y = await page.evaluate(
                "window.scrollY"
            )

            document_y = (
                box["y"] + scroll_y
            )

            candidates.append(
                {
                    "text": text,

                    "href": (
                        await element.get_attribute(
                            "href"
                        )
                    ),

                    "tag": tag,
                    "role": role,
                    "classes": classes,

                    "x": round(box["x"], 1),
                    "y": round(document_y, 1),

                    "width": round(
                        box["width"],
                        1,
                    ),

                    "height": round(
                        box["height"],
                        1,
                    ),

                    "area": round(
                        box["width"]
                        * box["height"],
                        1,
                    ),

                    "background": styles["bg"],
                    "color": styles["color"],
                    "font_size": styles["fontSize"],
                    "font_weight": styles["fontWeight"],
                    "border_radius": styles[
                        "borderRadius"
                    ],
                }
            )

        except Exception:
            # One problematic element should never stop
            # extraction for the whole page.
            continue

    return candidates


# ============================================================
# DEDUPLICATION
# ============================================================

def _deduplicate(
    items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove duplicate CTA candidates.

    Text + href + approximate vertical position are used
    because the same CTA can sometimes appear in multiple
    DOM wrappers.
    """

    seen = set()

    result = []

    for item in items:

        key = (
            normalize_text(
                item["text"]
            ),

            item.get("href") or "",

            round(
                item["y"] / 15
            ),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


# ============================================================
# VISUAL ANALYSIS
# ============================================================

def _has_visible_background(
    background: str,
) -> bool:
    """
    Determine whether the CTA has a visible background.
    """

    if not background:
        return False

    normalized = background.casefold()

    transparent_values = {
        "transparent",
        "rgba(0, 0, 0, 0)",
        "rgb(255, 255, 255)",
        "rgba(255, 255, 255, 0)",
    }

    return normalized not in transparent_values


def _prominence_score(
    cta: Dict[str, Any],
    viewport_height: int,
) -> int:
    """
    Assess visual CTA prominence on a 1-5 scale.

    Factors:
    - above fold
    - element size
    - font size / weight
    - colored background
    - button dimensions
    """

    score = 1

    # --------------------------------------------------------
    # Above fold
    # --------------------------------------------------------

    if cta["y"] < viewport_height:
        score += 1

    # --------------------------------------------------------
    # Area
    # --------------------------------------------------------

    area = cta.get("area", 0)

    if area >= 12000:
        score += 2

    elif area >= 6000:
        score += 1

    # --------------------------------------------------------
    # Typography
    # --------------------------------------------------------

    font_size = cta.get(
        "font_size",
        0,
    )

    font_weight = cta.get(
        "font_weight",
        400,
    )

    if font_size >= 18:
        score += 1

    elif font_size >= 16 and font_weight >= 600:
        score += 1

    # --------------------------------------------------------
    # Background
    # --------------------------------------------------------

    if _has_visible_background(
        cta.get("background", "")
    ):
        score += 1

    return min(
        5,
        score,
    )


def _position_score(
    cta: Dict[str, Any],
    viewport_height: int,
) -> int:
    """
    Score CTA position.

    3 = clearly above fold
    2 = near the first viewport
    1 = further down the page
    """

    y = cta.get("y", 999999)

    if y < viewport_height:
        return 3

    if y < viewport_height * 1.5:
        return 2

    return 1


# ============================================================
# CTA INTENT
# ============================================================

def _cta_intent_score(
    cta: Dict[str, Any],
) -> int:
    """
    Assign semantic intent strength.

    Strong transactional actions receive higher scores,
    while informational actions receive lower scores.
    """

    cta_type = classify_cta_type(
        cta["text"]
    )

    weights = {

        "Calculate": 10,
        "Apply": 10,
        "Buy": 10,
        "Open": 9,

        "Compare": 8,

        "Learn": 6,

        "Contact": 5,

        "Other": 2,
    }

    score = weights.get(
        cta_type,
        2,
    )

    # --------------------------------------------------------
    # CTA class bonus
    # --------------------------------------------------------

    if _has_cta_class(
        cta.get("classes", "")
    ):
        score += 2

    # --------------------------------------------------------
    # Strong action words
    # --------------------------------------------------------

    strong_action_phrases = (
        "now",
        "today",
        "online",
        "start",
        "get started",
        "calculate",
        "simulate",
        "simuleer",
        "bereken",
        "calculez",
        "compare",
        "vergelijk",
    )

    normalized_text = normalize_text(
        cta["text"]
    )

    if any(
        _contains_phrase(
            normalized_text,
            phrase,
        )
        for phrase in strong_action_phrases
    ):
        score += 1

    return score


# ============================================================
# PRIMARY CTA SELECTION
# ============================================================

def _primary_cta_score(
    cta: Dict[str, Any],
    viewport_height: int,
) -> tuple:
    """
    Calculate the ranking tuple for primary CTA selection.

    The order intentionally prioritizes what a human sees:

    1. Visual prominence
    2. Above-fold placement
    3. CTA intent
    4. CTA class
    5. Size
    6. Earlier page position
    """

    prominence = _prominence_score(
        cta,
        viewport_height,
    )

    position = _position_score(
        cta,
        viewport_height,
    )

    intent = _cta_intent_score(
        cta
    )

    area = cta.get(
        "area",
        0,
    )

    return (
        prominence,
        position,
        intent,
        area,
        -cta.get("y", 999999),
    )


def _select_primary(
    items: List[Dict[str, Any]],
    viewport_height: int,
) -> Optional[Dict[str, Any]]:
    """
    Select the CTA that best represents the page's
    visually primary call-to-action.
    """

    if not items:
        return None

    return max(
        items,
        key=lambda item:
        _primary_cta_score(
            item,
            viewport_height,
        ),
    )


# ============================================================
# MAIN EXTRACTION
# ============================================================

async def extract_cta_features(
    page: Page,
    url: str,
) -> Dict[str, Any]:
    """
    Extract CTA features from one rendered URL.
    """

    # --------------------------------------------------------
    # Load page
    # --------------------------------------------------------

    await page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=config.PAGE_TIMEOUT_MS,
    )

    # Some banking pages continue loading resources after
    # DOMContentLoaded. Network idle is helpful but not
    # mandatory.
    try:

        await page.wait_for_load_state(
            "networkidle",
            timeout=config.NETWORK_IDLE_TIMEOUT_MS,
        )

    except Exception:
        pass

    # --------------------------------------------------------
    # Scroll through page
    # --------------------------------------------------------

    scroll_js = """
    async (options) => {

        for (
            let i = 0;
            i < options.steps;
            i++
        ) {

            const before = window.scrollY;

            window.scrollBy(
                0,
                Math.max(
                    500,
                    window.innerHeight * 0.8
                )
            );

            await new Promise(
                resolve =>
                    setTimeout(
                        resolve,
                        options.pause
                    )
            );

            if (
                window.scrollY === before
            ) {
                break;
            }
        }

        window.scrollTo(0, 0);

        await new Promise(
            resolve =>
                setTimeout(
                    resolve,
                    options.pause
                )
        );
    }
    """

    await page.evaluate(
        scroll_js,
        {
            "steps": config.MAX_SCROLL_STEPS,
            "pause": config.SCROLL_PAUSE_MS,
        },
    )

    # --------------------------------------------------------
    # Collect and deduplicate
    # --------------------------------------------------------

    items = await _collect_candidates(
        page
    )

    items = _deduplicate(
        items
    )

    # --------------------------------------------------------
    # Select primary CTA
    # --------------------------------------------------------

    viewport_height = config.VIEWPORT[
        "height"
    ]

    primary = _select_primary(
        items,
        viewport_height,
    )

    # --------------------------------------------------------
    # Repetition
    # --------------------------------------------------------

    normalized_texts = [
        normalize_text(
            item["text"]
        )
        for item in items
    ]

    text_counts = Counter(
        normalized_texts
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "cta_count": len(items),

        "primary_cta_text": (
            primary["text"]
            if primary
            else None
        ),

        "cta_above_fold": (
            bool(
                primary
                and primary["y"]
                < viewport_height
            )
        ),

        "cta_repeated": (
            bool(
                primary
                and text_counts[
                    normalize_text(
                        primary["text"]
                    )
                ] > 1
            )
        ),

        "cta_prominence": (
            _prominence_score(
                primary,
                viewport_height,
            )
            if primary
            else 1
        ),

        "cta_type": (
            classify_cta_type(
                primary["text"]
            )
            if primary
            else "Other"
        ),
    }

    # --------------------------------------------------------
    # Optional debug information
    # --------------------------------------------------------

    if config.DEBUG_DETECTED_CTAS:

        result["detected_ctas"] = [

            {
                "text": item["text"],

                "type": classify_cta_type(
                    item["text"]
                ),

                "above_fold": (
                    item["y"]
                    < viewport_height
                ),

                "prominence": (
                    _prominence_score(
                        item,
                        viewport_height,
                    )
                ),

                "intent_score": (
                    _cta_intent_score(
                        item
                    )
                ),

                "position_score": (
                    _position_score(
                        item,
                        viewport_height,
                    )
                ),

                "area": item["area"],

                "y": item["y"],
            }

            for item in items
        ]

    return result