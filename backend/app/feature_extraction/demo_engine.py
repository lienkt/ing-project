"""DEMO ONLY. Fixed semantic examples, not NLP, AI, or research evidence."""
from app.scraping.contracts import ScrapedPage
from app.schemas.features import FeatureInput
from app.feature_extraction.contracts import FeatureSuggestions


class DemoFeatureExtractionEngine:
    name = "demo"
    is_demo = True

    def extract(self, page: ScrapedPage) -> FeatureSuggestions:
        return FeatureSuggestions(is_demo=True, warnings=["DEMO ONLY: review every suggestion."],
            values=FeatureInput(word_count=len(page.text.split()), heading_count=len(page.headings),
                paragraph_count=len(page.paragraphs), image_count=len(page.images),
                cta_count=len(page.buttons), tone_formality=3, tone_friendliness=4, visual_intensity=2,
                product_name=page.source.product_name, language=page.source.language,
                bank_type=page.source.bank_type, capture_date=page.scraped_at.date()))
