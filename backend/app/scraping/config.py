"""Supported scraping cases — edit this list when adding a finished scraper.

1. Implement the function in functions.py or a bank-specific file.
2. Test it.
3. Import it here and add its exact normalized case below.
Unregistered cases require manual scraping. Never register unfinished functions.
"""

from app.schemas.automation import build_case_key
from app.scraping.functions import scrape_demo_page

# Explicit DEMO cases only. Everything else requires manual collection.
SCRAPING_SUPPORT = {
    build_case_key(
        "ING", "Current Account", "ING example current account", "EN"
    ): scrape_demo_page,
    build_case_key(
        "KBC", "Current Account", "KBC example current account", "EN"
    ): scrape_demo_page,
}
