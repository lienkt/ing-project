"""DEMO ONLY. No network access. Replace with a real scraping engine."""
from datetime import datetime, timezone
from app.scraping.contracts import SourceDefinition, ScrapedPage


class DemoScrapingEngine:
    name = "demo"
    is_demo = True

    def scrape(self, source: SourceDefinition) -> ScrapedPage:
        paragraphs = [f"Demo content for {source.bank}. This is not collected website evidence.",
                      "Explore example account features and everyday banking benefits."]
        return ScrapedPage(source=source, title=f"Demo {source.product_name}",
                           text="\n".join(paragraphs), paragraphs=paragraphs,
                           headings=[source.product_name, "Example benefits"],
                           buttons=["Open account", "Learn more"], sections=["Overview", "Benefits"],
                           scraped_at=datetime.now(timezone.utc), is_demo=True,
                           warnings=["DEMO ONLY: synthetic content; no webpage was fetched."])
