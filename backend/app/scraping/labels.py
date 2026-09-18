"""Label functions receive (CampaignInformation, ScrapedPage) and return FeatureSuggestions.

Use existing FeatureInput fields/enums. Omit unknown fields and the derived
average_paragraph_length. Never write labels, set Completed, or replace analyst
notes here. The collection service saves the automatic draft during scraping.
"""

from app.schemas.automation import CampaignInformation, ScrapedPage, FeatureSuggestions
from app.schemas.features import FeatureInput


def label_demo_page(
    campaign: CampaignInformation, scraped_data: ScrapedPage
) -> FeatureSuggestions:
    """DEMO ONLY. Counts plus fixed example scores; no real analysis."""
    return FeatureSuggestions(
        is_demo=True,
        warnings=["DEMO ONLY: review every suggestion."],
        values=FeatureInput(
            word_count=len(scraped_data.text.split()),
            heading_count=len(scraped_data.headings),
            paragraph_count=len(scraped_data.paragraphs),
            image_count=len(scraped_data.images),
            cta_count=len(scraped_data.buttons),
            tone_formality=3,
            tone_friendliness=4,
            visual_intensity=2,
            product_name=campaign.product_name,
            language=scraped_data.source.language,
            bank_type=scraped_data.source.bank_type,
            capture_date=scraped_data.scraped_at.date(),
        ),
    )


def collected_feature_values(page: ScrapedPage) -> FeatureInput:
    """Measured values only; counts describe the captured text, not hidden content."""
    from app.scraping.functions import count_words

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
    return FeatureInput(**values)


def label_ing_youth_account_en(
    campaign: CampaignInformation, scraped_data: ScrapedPage
) -> FeatureSuggestions:
    """Rule-based text suggestions for the registered ING case; requires review."""
    from app.scraping.functions import count_words
    from app.scraping.scrapping_pipeline import (
        calculate_text_density,
        calculate_text_style,
        calculate_information_complexity,
    )

    values = collected_feature_values(scraped_data).model_dump(exclude_unset=True)
    words = values["word_count"]
    headings = values["heading_count"]
    paragraphs = values["paragraph_count"]
    paragraph_average = (
        sum(count_words(p) for p in scraped_data.paragraphs) / paragraphs
        if paragraphs
        else 0
    )
    from app.scraping.config import DEFAULT_FINANCIAL_TERMS_EN

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
        is_demo=False,
        warnings=[
            "Rule-based suggestions, not AI analysis. Review text style and density before saving.",
            "Counts cover extracted content only. Hidden FAQ may be missing; images, CTA, tone and visual labels remain unset.",
        ],
    )
