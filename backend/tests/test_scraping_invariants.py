"""Architecture contracts without live websites or database migrations."""

import asyncio
import json
from datetime import datetime, UTC
from pathlib import Path

import pytest

from app.schemas.automation import ManualRequired, ScrapedPage, build_case_key
from app.scraping import capture, scraping_config
from app.scraping.dispatcher import (
    auto_label_campaign,
    auto_label_support,
    has_auto_labels,
    scrape_campaign,
    scraping_support,
)
from app.scraping.feature_labels import collected_feature_values
from app.scraping.page_scrapers import scrape_ing_youth_account_en
from app.services.source_catalog import load_sources

# Pin existing support so removing a catalog entry cannot silently shrink coverage.
REGISTERED_IDS = (
    "ing-youth-account-en",
    "argenta-messages-savings-account-fr",
    "belfius-messages-investment-fr",
    "beobank-messages-car-insurance-nl",
    "crelan-messages-savings-account-nl",
    "ing-messages-car-insurance-en",
    "kbc-messages-home-insurance-en",
)


@pytest.fixture
def source():
    return next(s for s in load_sources() if s.source_id == "ing-youth-account-en")


@pytest.mark.parametrize("source_id", REGISTERED_IDS)
def test_production_cases_keep_real_handlers(source_id):
    case = next(s for s in load_sources() if s.source_id == source_id)
    key = build_case_key(
        case.bank, case.product_category, case.product_name, case.language
    )
    handlers = scraping_config.AUTO_SUPPORT[key]
    assert callable(handlers["scrape"]) and callable(handlers["label"])
    assert scraping_support(case)["supported"] and has_auto_labels(case)
    if source_id == "ing-youth-account-en":
        assert handlers["scrape"] is scrape_ing_youth_account_en
    else:
        assert handlers["scrape"] is scraping_config.scrape_message_page
        assert handlers["label"] is scraping_config.label_message_page


@pytest.mark.parametrize(
    "changes",
    [
        {"bank": "Unregistered bank"},
        {"product_category": "savings_account"},
        {"product_name": "ING Youth Account Plus"},
        {"language": "French"},
    ],
)
def test_each_identity_component_gates_specialized_dispatch(source, changes):
    case = source.model_copy(update=changes)
    page = ScrapedPage(
        source=case, title="Product", text="Product text", scraped_at=datetime.now(UTC)
    )
    assert not scraping_support(case)["supported"]
    assert not has_auto_labels(case)
    assert isinstance(scrape_campaign(case), ManualRequired)
    assert isinstance(auto_label_campaign(case, page), ManualRequired)


@pytest.mark.parametrize("invalid", ["failed", "other_url"])
def test_registered_labeling_requires_successful_matching_evidence(source, invalid):
    page = ScrapedPage(
        source=source,
        title="Product",
        text="Product text",
        scraped_at=datetime.now(UTC),
    )
    if invalid == "failed":
        page.success = False
        page.error = "Capture failed"
    else:
        page.source = source.model_copy(update={"url": "https://example.com/other"})
    support = auto_label_support(source, page)
    assert support["supported"] and not support["available"]
    assert isinstance(auto_label_campaign(source, page), ManualRequired)


@pytest.mark.parametrize("measured", [None, 0])
def test_unmeasured_counts_stay_missing_and_measured_zero_survives(source, measured):
    page = ScrapedPage(
        source=source,
        title="Product",
        text="Product text",
        bullet_list_count=measured,
        scraped_at=datetime.now(UTC),
    )
    values = collected_feature_values(page)
    assert values.word_count == 2
    assert values.bullet_list_count is measured
    for name in ("image_count", "cta_count", "headline_length", "tone_formality"):
        assert getattr(values, name) is None
        assert name not in values.model_dump(exclude_unset=True)
    assert ("bullet_list_count" in values.model_fields_set) == (measured is not None)


@pytest.mark.parametrize("sync", [False, True], ids=["async", "sync"])
@pytest.mark.parametrize("failure", [None, "screenshot", "dom"])
def test_capture_writers_save_evidence_or_remove_partial_artifacts(
    tmp_path, monkeypatch, sync, failure
):
    monkeypatch.setattr(capture, "ROOT", tmp_path)
    dom = {
        "html": "<html>épargne</html>",
        "shadow_roots": [{"host": "product", "html": "<p>Evidence</p>"}],
    }

    class Page:
        def screenshot(self, *, path, full_page):
            assert full_page
            Path(path).write_bytes(b"screenshot fixture")
            if failure == "screenshot":
                raise RuntimeError("screenshot failed")

        def evaluate(self, script):
            assert script == capture.DOM_SCRIPT
            if failure == "dom":
                raise RuntimeError("dom failed")
            return dom

    class AsyncPage(Page):
        async def screenshot(self, **kwargs):
            return super().screenshot(**kwargs)

        async def evaluate(self, script):
            return super().evaluate(script)

    def run():
        if sync:
            return capture.capture_evidence_sync(Page())
        return asyncio.run(capture.capture_evidence(AsyncPage()))

    if failure:
        with pytest.raises(RuntimeError, match=failure):
            run()
        assert list(tmp_path.iterdir()) == []
    else:
        artifact_id = run()
        assert capture.artifact_path(artifact_id, "screenshot.png").stat().st_size > 0
        assert (
            json.loads(
                capture.artifact_path(artifact_id, "dom.json").read_text(
                    encoding="utf-8"
                )
            )
            == dom
        )
