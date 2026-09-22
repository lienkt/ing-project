"""Real scraper adapter tests without external website requests."""

import asyncio
import pytest
from app.scraping import page_scrapers as functions, text_scoring as pipeline
from app.scraping.dispatcher import scrape_campaign
from app.schemas.automation import ScrapedPage
from app.services.source_catalog import load_sources
from test_campaigns import client


def real_source():
    return next(s for s in load_sources() if s.source_id == "ing-youth-account-en")


def test_real_case_import_prefills_draft_and_supports_labeling(client, monkeypatch):
    async def collect(config, browser):
        assert config.language == "en" and config.product == "ING Youth Account"
        assert config.clean_page is False
        assert config.main_selector == "ing-feat-flexible-page"
        assert config.ready_selector == "ing-feat-flexible-page flex-productheader h1"
        return dict(
            headline="Youth account",
            all_text="Youth account Save money",
            headings=["Youth account"],
            paragraphs=["Save money"],
            bullets=["No monthly fee"],
            tables=["Rate 0%"],
            bullet_list_count=1,
            final_url=config.url,
        )

    class Browser:
        async def close(self):
            self.closed = True

    browser = Browser()

    class Chromium:
        async def launch(self, **kwargs):
            return browser

    class Playwright:
        chromium = Chromium()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr("playwright.async_api.async_playwright", Playwright)
    monkeypatch.setattr(functions, "scrape_site", collect)
    page = scrape_campaign(real_source())
    assert browser.closed
    assert ScrapedPage.model_validate_json(page.model_dump_json()).tables == ["Rate 0%"]
    result = client.post(
        "/api/scraping/run", json={"source_ids": [real_source().source_id]}
    ).json()["results"][0]
    assert result["status"] == "success"
    campaign_id = result["campaign_id"]
    data = client.get(f"/api/campaigns/{campaign_id}/features").json()
    assert data["labeling_status"] == "In Progress"
    assert data["features"]["product_name"] == "ING Youth Account"
    assert data["features"]["word_count"] == 4
    assert data["features"]["image_count"] is None
    assert data["features"]["tone_formality"] is None
    assert data["features"]["text_style"] == "Concise"
    assert data["features"]["text_density"] == 1
    assert data["features"]["information_complexity"] == 1
    client.put(f"/api/campaigns/{campaign_id}/features", json={"word_count": 123})
    client.post(
        "/api/scraping/run",
        json={"source_ids": [real_source().source_id], "recapture": True},
    )
    assert (
        client.get(f"/api/campaigns/{campaign_id}/features").json()["features"][
            "word_count"
        ]
        == 123
    )



def test_http_error_is_not_content():
    class Response:
        status = 403

    class Page:
        async def goto(self, *args, **kwargs):
            return Response()

    with pytest.raises(ValueError, match="403"):
        asyncio.run(functions.load_page(Page(), "https://www.ing.be"))


def test_shared_text_helpers():
    from app.scraping import message_analysis as function_messages

    assert functions.count_words is function_messages.count_words
    assert functions.clean_text is function_messages.clean_text
    text = "  Épargne\xa0 sans-frais\n aujourd'hui  "
    assert functions.clean_text(text) == "Épargne sans-frais aujourd'hui"
    assert functions.count_words(text) == 3
    assert functions.count_words("") == 0


def test_french_scoring_requires_explicit_vocabulary():
    from app.scraping.scraping_config import SiteConfig

    config = SiteConfig(
        bank="ING", product="Account", url="https://www.ing.be", language="fr"
    )
    with pytest.raises(ValueError, match="financial_terms"):
        config.terms()
    config.financial_terms = ("intérêt",)
    assert config.terms() == ("intérêt",)


@pytest.mark.parametrize(
    "changes",
    [
        {"bank": "KBC"},
        {"product_category": "Savings Account"},
        {"product_name": "Another ING account"},
        {"language": "Dutch"},
    ],
)
def test_ing_case_rejects_other_cases_before_browser_launch(changes):
    with pytest.raises(ValueError, match="only supports"):
        functions.scrape_ing_youth_account_en(real_source().model_copy(update=changes))


def test_unregistered_product_does_not_fall_back_to_generic_scraper():
    from app.schemas.automation import ManualRequired

    source = real_source().model_copy(update={"product_name": "Another ING account"})
    assert isinstance(scrape_campaign(source), ManualRequired)


def test_scoped_capture_does_not_destroy_component_tree(monkeypatch):
    from app.scraping.scraping_config import SiteConfig

    class Locator:
        @property
        def first(self):
            return self

        async def wait_for(self, **kwargs):
            pass

    class Page:
        url = "https://www.ing.be/test"

        def locator(self, selector):
            assert selector in {"ing-feat-flexible-page", "ing-feat-flexible-page h1"}
            return Locator()

    class Context:
        closed = False

        async def new_page(self):
            return Page()

        async def close(self):
            self.closed = True

    context = Context()

    class Browser:
        async def new_context(self, **kwargs):
            return context

    async def load(*args, **kwargs):
        pass

    async def capture(page):
        return "test-artifact"

    async def destructive_cleanup(page):
        pytest.fail("Global cleanup must not run for the scoped ING component")

    async def extract(main, **kwargs):
        return {
            "headline": "Youth account",
            "headings": [],
            "paragraphs": ["Product content"],
            "bullets": [],
            "tables": [],
            "bullet_list_count": 0,
        }

    monkeypatch.setattr(functions, "load_page", load)
    monkeypatch.setattr(functions, "remove_noise", destructive_cleanup)
    monkeypatch.setattr(functions, "extract_content", extract)
    monkeypatch.setattr("app.scraping.capture.capture_evidence", capture)
    config = SiteConfig(
        bank="ING",
        product="Youth",
        url=Page.url,
        clean_page=False,
        main_selector="ing-feat-flexible-page",
        ready_selector="ing-feat-flexible-page h1",
    )
    result = asyncio.run(functions.scrape_site(config, Browser()))
    assert "Product content" in result["all_text"]
    assert result["artifact_id"] == "test-artifact"
    assert context.closed
