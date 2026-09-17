"""Contracts and API workflow on a disposable, migrated database."""
import json
import pytest
from pydantic import ValidationError
from app.main import app
from app.core.config import settings
from app.scraping.contracts import ScrapedPage
from app.scraping.demo_engine import DemoScrapingEngine
from app.scraping.engine import get_scraping_engine
from app.feature_extraction.demo_engine import DemoFeatureExtractionEngine
from app.feature_extraction.contracts import FeatureSuggestions
from app.feature_extraction.engine import get_feature_extraction_engine
from app.services.source_catalog import load_sources, CatalogError
from test_campaigns import client, create


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "data_mode", "demo")


def import_one(client):
    source = client.get("/api/scraping/sources").json()["sources"][0]
    response = client.post("/api/scraping/run", json={"source_ids": [source["source_id"]]})
    assert response.status_code == 200, response.text
    result = response.json()["results"][0]
    assert result["status"] == "success", result
    return result["campaign_id"]


def test_contracts():
    source = load_sources()[0]
    page = ScrapedPage.model_validate(DemoScrapingEngine().scrape(source).model_dump())
    assert page.source == source and page.is_demo and page.success
    engine = DemoFeatureExtractionEngine()
    result = FeatureSuggestions.model_validate(engine.extract(page).model_dump(exclude_unset=True))
    assert result.values.word_count > 0
    assert result.values.image_count == 0
    assert engine.extract(page) == engine.extract(page)
    for values in ({"tone_formality": 6}, {"word_count": -1}, {"language": "EN"},
                   {"average_paragraph_length": 3}, {"word_count": True}, {"labeling_notes": "overwrite"}, {}):
        with pytest.raises(ValidationError):
            FeatureSuggestions(values=values, is_demo=True)


def test_catalog_validation(tmp_path):
    with pytest.raises(CatalogError, match="empty"):
        load_sources(tmp_path)
    file = tmp_path / "broken.json"
    file.write_text('{"sources": [{}]}')
    with pytest.raises(CatalogError, match="broken.json"):
        load_sources(tmp_path)
    source = load_sources()[0].model_dump(mode="json")
    file.write_text(json.dumps({"sources": [source, source]}))
    with pytest.raises(CatalogError, match="Duplicate source_id"):
        load_sources(tmp_path)


def test_catalog_is_not_dataset_and_filters(client):
    assert client.get("/api/campaigns").json() == []
    response = client.get("/api/scraping/sources", params={"bank": "ing", "product_category": "current_account"})
    assert response.status_code == 200
    assert [s["bank"] for s in response.json()["sources"]] == ["ING"]
    assert all(s["is_example"] for s in response.json()["sources"])
    assert client.get("/api/campaigns").json() == []


def test_partial_batch_and_unknown_source(client):
    class PartialEngine(DemoScrapingEngine):
        def scrape(self, source):
            if source.bank == "KBC":
                raise ValueError("Example source failure")
            return super().scrape(source)
    app.dependency_overrides[get_scraping_engine] = PartialEngine
    ids = [s.source_id for s in load_sources()] + ["unknown"]
    result = client.post("/api/scraping/run", json={"source_ids": ids}).json()["results"]
    assert [r["status"] for r in result] == ["success", "failed", "success", "failed"]
    assert len(client.get("/api/campaigns").json()) == 2
    catalog = client.get("/api/scraping/sources").json()["sources"]
    failed = next(s for s in catalog if s["bank"] == "KBC")
    assert failed["import_status"] == "Failed" and "Example source failure" in failed["error"]
    app.dependency_overrides.pop(get_scraping_engine)
    retried = client.post("/api/scraping/run", json={"source_ids": [failed["source_id"]]}).json()["results"][0]
    assert retried["status"] == "success"


def test_duplicate_import_and_delete(client):
    campaign_id = import_one(client)
    source_id = load_sources()[0].source_id
    result = client.post("/api/scraping/run", json={"source_ids": [source_id, source_id]}).json()["results"]
    assert result == [{"source_id": source_id, "status": "existing", "campaign_id": campaign_id, "error": None}]
    assert len(client.get("/api/campaigns").json()) == 1
    client.post(f"/api/campaigns/{campaign_id}/auto-label")
    assert client.delete(f"/api/campaigns/{campaign_id}").status_code == 204
    assert client.get("/api/scraping/sources").json()["sources"][0]["import_status"] == "Ready"
    import_one(client)


def test_existing_manual_url_is_not_overwritten(client):
    source = load_sources()[0]
    original = client.post("/api/campaigns", json={"bank_name": source.bank, "project": source.product_category,
                                                  "campaign_url": str(source.url) + "#section"}).json()
    result = client.post("/api/scraping/run", json={"source_ids": [source.source_id]}).json()["results"][0]
    assert result["status"] == "existing" and result["campaign_id"] == original["id"]
    assert client.get(f"/api/campaigns/{original['id']}").json()["collection"] is None
    assert client.post(f"/api/campaigns/{original['id']}/auto-label").status_code == 409


def test_auto_requires_scraped_page_and_known_campaign(client):
    campaign = create(client)
    assert client.post(f"/api/campaigns/{campaign['id']}/auto-label").status_code == 409
    assert client.post("/api/campaigns/999/auto-label").status_code == 404


def test_import_suggest_review_complete_compare(client):
    campaign_id = import_one(client)
    base = f"/api/campaigns/{campaign_id}"
    campaign = client.get(base).json()
    assert campaign["collection"]["is_demo"] and campaign["collection"]["status"] == "Scraped"
    assert campaign["labeling_status"] == "Not Started"
    proposal = client.post(base + "/auto-label").json()
    assert proposal["is_demo"] and not proposal["reviewed"]
    assert client.get(base).json()["has_suggestions"]
    assert client.get(base + "/features").json()["features"] is None
    assert client.get("/api/compare?product_category=current_account").json()["pages"][0]["features"] is None
    values = {**proposal["values"], "tone_formality": 5, "tone_friendliness": None}
    reviewed = client.post(base + "/suggestions/review", json={"token": proposal["token"], "values": values})
    assert reviewed.status_code == 200, reviewed.text
    data = reviewed.json()
    assert data["labeling_status"] == "In Progress"
    assert data["features"]["source"] == "manual_override"
    assert data["features"]["tone_formality"] == 5
    assert data["features"]["tone_friendliness"] is None
    assert not client.get(base).json()["has_suggestions"]
    assert client.post(base + "/features/complete", json={"confirm_incomplete": True}).json()["labeling_status"] == "Completed"
    page = client.get("/api/compare?product_category=current_account").json()["pages"][0]
    assert page["features"]["tone_formality"] == 5 and page["features"]["image_count"] == 0
    assert page["labeling_status"] == "Completed"
    assert client.post(base + "/suggestions/review", json={"token": proposal["token"], "values": values}).status_code == 409


def test_manual_values_survive_generation_and_stale_review(client):
    campaign_id = import_one(client)
    base = f"/api/campaigns/{campaign_id}"
    client.put(base + "/features", json={"word_count": 999, "labeling_notes": "Keep my notes"})
    client.post(base + "/features/complete", json={"confirm_incomplete": True})
    before = client.get(base + "/features").json()["features"]
    proposal = client.post(base + "/auto-label").json()
    assert client.get(base + "/features").json()["features"] == before
    client.put(base + "/features", json={"word_count": 1000})
    assert client.post(base + "/suggestions/review", json={"token": proposal["token"], "values": proposal["values"]}).status_code == 409
    assert client.get(base + "/features").json()["features"]["word_count"] == 1000


def test_replaced_proposal_token_rejected(client):
    base = f"/api/campaigns/{import_one(client)}"
    old = client.post(base + "/auto-label").json()
    new = client.post(base + "/auto-label").json()
    assert old["token"] != new["token"]
    assert client.post(base + "/suggestions/review", json={"token": old["token"], "values": old["values"]}).status_code == 409


def test_invalid_engine_output_isolated(client):
    class InvalidScraper(DemoScrapingEngine):
        def scrape(self, source):
            return super().scrape(source).model_copy(update={"headings": "invalid"})
    app.dependency_overrides[get_scraping_engine] = InvalidScraper
    result = client.post("/api/scraping/run", json={"source_ids": [load_sources()[0].source_id]}).json()
    assert result["results"][0]["status"] == "failed"
    assert client.get("/api/campaigns").json() == []
    app.dependency_overrides.pop(get_scraping_engine)
    campaign_id = import_one(client)
    class InvalidExtractor(DemoFeatureExtractionEngine):
        def extract(self, page):
            result = super().extract(page)
            result.values.tone_formality = 99
            return result
    app.dependency_overrides[get_feature_extraction_engine] = InvalidExtractor
    assert client.post(f"/api/campaigns/{campaign_id}/auto-label").status_code == 422
    assert client.get(f"/api/campaigns/{campaign_id}/suggestions").json() is None


def test_demo_engines_block_real_database(client, monkeypatch):
    campaign_id = import_one(client)
    proposal = client.post(f"/api/campaigns/{campaign_id}/auto-label").json()
    monkeypatch.setattr(settings, "data_mode", "real")
    assert client.post("/api/scraping/run", json={"source_ids": [load_sources()[1].source_id]}).status_code == 409
    assert client.post(f"/api/campaigns/{campaign_id}/auto-label").status_code == 409
    assert client.post(f"/api/campaigns/{campaign_id}/suggestions/review", json={"token": proposal["token"], "values": proposal["values"]}).status_code == 409


def test_changed_campaign_url_blocks_extraction(client):
    campaign_id = import_one(client)
    base = f"/api/campaigns/{campaign_id}"
    client.put(base, json={"bank_name": "ING", "project": "current_account", "campaign_url": "https://example.com/changed"})
    assert client.post(base + "/auto-label").status_code == 409


def test_migration_matches_models(client):
    from alembic import command
    from alembic.config import Config
    command.check(Config("alembic.ini"))
