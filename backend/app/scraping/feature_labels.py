"""Label functions receive (CampaignInformation, ScrapedPage) and return FeatureSuggestions.

Use existing FeatureInput fields/enums. Omit unknown fields and the derived
average_paragraph_length. Never write labels, set Completed, or replace analyst
notes here. The collection service saves the automatic draft during scraping.
"""

import json

from app.schemas.automation import CampaignInformation, FeatureSuggestions, ScrapedPage
from app.schemas.features import FeatureInput
from app.scraping.message_analysis import count_words
from app.scraping.text_scoring import (
    calculate_information_complexity,
    calculate_text_density,
    calculate_text_style,
)


def collected_feature_values(page: ScrapedPage) -> FeatureInput:
    """Measured values only; counts describe the captured text, not hidden content."""

    values = dict(
        product_name=page.source.product_name,
        language=page.source.language,
        bank_type=page.source.bank_type,
        capture_date=page.scraped_at.date(),
        word_count=count_words(page.text),
        heading_count=len(page.headings),
        paragraph_count=len(page.paragraphs),
    )
    if page.headline is not None:
        values["headline_length"] = count_words(page.headline)
    if page.bullet_list_count is not None:
        values["bullet_list_count"] = page.bullet_list_count

    if "cta_features" in page.metadata:
        cta = json.loads(page.metadata["cta_features"])
        for field in (
            "cta_count",
            "primary_cta_text",
            "cta_above_fold",
            "cta_repeated",
            "cta_prominence",
            "cta_type",
        ):
            if field in cta:
                values[field] = cta[field]
    return FeatureInput(**values)


def label_ing_youth_account_en(
    campaign: CampaignInformation, scraped_data: ScrapedPage
) -> FeatureSuggestions:
    """Rule-based text suggestions for the registered ING case; requires review."""

    values = collected_feature_values(scraped_data).model_dump(exclude_unset=True)
    words = values["word_count"]
    headings = values["heading_count"]
    paragraphs = values["paragraph_count"]
    paragraph_average = (
        sum(count_words(p) for p in scraped_data.paragraphs) / paragraphs
        if paragraphs
        else 0
    )
    # scraping_config registers this handler; defer the import to avoid a cycle.
    from app.scraping.scraping_config import DEFAULT_FINANCIAL_TERMS_EN

    values["information_complexity"] = calculate_information_complexity(
        scraped_data.text, words, headings, DEFAULT_FINANCIAL_TERMS_EN
    )
    values["text_style"] = calculate_text_style(words, paragraph_average, headings)
    if scraped_data.bullet_list_count is not None:
        values["text_density"] = calculate_text_density(
            words, headings, paragraphs, scraped_data.bullet_list_count
        )
    return FeatureSuggestions(
        values=FeatureInput(**values),
        warnings=scraped_data.warnings
        + [
            "Rule-based suggestions, not AI analysis. Review text style and density before saving.",
            "Counts cover extracted content only. Hidden FAQ may be missing; images, tone and visual labels remain unset.",
        ],
    )
