"""CTA vocabulary, ranking, and app label integration."""

from datetime import datetime, timezone
import asyncio
import json

import pytest
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

from app.scraping.cta_analysis import (
    classify_cta_type,
    extract_loaded_cta_features,
    extract_loaded_cta_features_sync,
    summarize_candidates,
)
from app.scraping.feature_labels import collected_feature_values
from app.schemas.automation import ScrapedPage, SourceDefinition


@pytest.mark.parametrize(
    "text,expected",
    [
        ("OPEN AN ACCOUNT", "Open"),
        ("Découvrir", "Learn"),
        ("Bereken uw premie", "Calculate"),
        ("reopened", "Other"),
        ("Request more information", "Learn"),
    ],
)
def test_classification(text, expected):
    assert classify_cta_type(text) == expected


HTML = """<style>button { width:200px;height:50px;background:orange;font-weight:700; }</style>
<nav><button>Apply now</button></nav>
<button>Accept all cookies</button>
<button style="display:none">Buy now</button>
<button>Open an account</button>
<div style="height:1100px"></div><button>Open an account</button>"""


def test_rendered_cta_sync_async_and_label_mapping():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_content(HTML)
        sync_result = extract_loaded_cta_features_sync(page)
        browser.close()

    async def collect():
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1440, "height": 900})
            await page.set_content(HTML)
            result = await extract_loaded_cta_features(page)
            await browser.close()
            return result

    assert asyncio.run(collect()) == sync_result
    assert sync_result == dict(
        cta_count=2,
        primary_cta_text="Open an account",
        cta_above_fold=True,
        cta_repeated=True,
        cta_prominence=5,
        cta_type="Open",
    )
    source = SourceDefinition(
        source_id="cta-test",
        bank="ING",
        bank_type="Traditional",
        product_name="Test",
        product_category="current_account",
        language="English",
        page_type="Product Page",
        url="https://example.com/product",
    )
    page = ScrapedPage(
        source=source,
        title="Test",
        scraped_at=datetime.now(timezone.utc),
        text="Test product",
        metadata={"cta_features": json.dumps(sync_result)},
    )
    values = collected_feature_values(page).model_dump()
    assert {key: values[key] for key in sync_result} == sync_result
    assert (
        collected_feature_values(
            ScrapedPage(
                source=source,
                text="Test",
                title="Test",
                scraped_at=datetime.now(timezone.utc),
            )
        ).cta_count
        is None
    )


def test_empty_page_preserves_original_defaults():
    assert summarize_candidates([], 900) == dict(
        cta_count=0,
        primary_cta_text=None,
        cta_above_fold=False,
        cta_repeated=False,
        cta_prominence=1,
        cta_type="Other",
    )


def test_cta_saved_by_auto_label_and_preserved_on_recapture(client, monkeypatch):
    from app.scraping import message_scraper
    from test_message_integration import content
    from app.services.source_catalog import load_sources

    source = next(
        s for s in load_sources() if s.source_id.startswith("argenta-messages")
    )
    metrics = dict(
        cta_count=2,
        primary_cta_text="Open an account",
        cta_above_fold=True,
        cta_repeated=True,
        cta_prominence=5,
        cta_type="Open",
    )
    monkeypatch.setattr(
        "app.scraping.public_urls.validate_public_url", lambda url: None
    )
    monkeypatch.setattr(
        "app.scraping.capture.capture_evidence_sync", lambda page: "test-artifact"
    )
    monkeypatch.setattr(
        "app.scraping.cta_analysis.extract_loaded_cta_features_sync",
        lambda page: dict(metrics),
    )

    def render(url, capture):
        data = content()
        data["artifact_id"] = capture(object())
        return data

    monkeypatch.setattr(message_scraper, "render_page", render)
    result = client.post(
        "/api/scraping/run",
        json={"source_ids": [source.source_id], "mode": "scrape_and_label"},
    ).json()["results"][0]
    assert result["status"] == "success", result
    url = f"/api/campaigns/{result['campaign_id']}/features"
    saved = client.get(url).json()["features"]
    assert {key: saved[key] for key in metrics} == metrics
    metrics["cta_count"] = 8
    result = client.post(
        "/api/scraping/run",
        json={
            "source_ids": [source.source_id],
            "mode": "capture_only",
            "recapture": True,
        },
    ).json()["results"][0]
    assert result["status"] == "success", result
    assert client.get(url).json()["features"]["cta_count"] == 2


from test_campaigns import client
