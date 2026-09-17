from typing import Protocol
from app.core.config import settings
from app.scraping.contracts import ScrapedPage
from app.feature_extraction.contracts import FeatureSuggestions


class FeatureExtractionEngine(Protocol):
    name: str
    is_demo: bool

    def extract(self, page: ScrapedPage) -> FeatureSuggestions: ...


def get_feature_extraction_engine() -> FeatureExtractionEngine:
    """Register a real implementation here; no route/frontend changes needed."""
    if settings.feature_extraction_engine == "demo":
        from app.feature_extraction.demo_engine import DemoFeatureExtractionEngine
        return DemoFeatureExtractionEngine()
    raise ValueError(f"Unsupported FEATURE_EXTRACTION_ENGINE: {settings.feature_extraction_engine}")
