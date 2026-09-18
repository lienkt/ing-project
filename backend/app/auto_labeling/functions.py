"""Label functions receive (CampaignInformation, ScrapedPage) and return FeatureSuggestions.

Use existing FeatureInput fields/enums. Omit unknown fields and the derived
average_paragraph_length. Never write labels, set Completed, or replace analyst
notes here. The existing review service handles suggestions and explicit saves.
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


def label_ing_current_account_lion_en(
    campaign: CampaignInformation, scraped_data: ScrapedPage
) -> FeatureSuggestions:
    """TODO: teammate implements feature extraction. Keep unregistered until ready."""
    raise NotImplementedError("ING Lion Account labeling is not implemented")
