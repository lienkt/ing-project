from typing import Protocol
from app.core.config import settings
from app.scraping.contracts import SourceDefinition, ScrapedPage


class ScrapingEngine(Protocol):
    name: str
    is_demo: bool

    def scrape(self, source: SourceDefinition) -> ScrapedPage: ...


def get_scraping_engine() -> ScrapingEngine:
    """Register a real implementation here; routes depend only on the protocol."""
    if settings.scraping_engine == "demo":
        from app.scraping.demo_engine import DemoScrapingEngine
        return DemoScrapingEngine()
    raise ValueError(f"Unsupported SCRAPING_ENGINE: {settings.scraping_engine}")
