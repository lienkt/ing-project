"""Case matching and import → suggestion → review integration on migrated databases."""

import json
import pytest
from pydantic import ValidationError
from app.core.config import settings
from app.schemas.automation import (
    ScrapedPage,
    SourceDefinition,
    FeatureSuggestions,
    ManualRequired,
    build_case_key,
)
from app.scraping import config as scraping
from app.scraping.dispatcher import scrape_campaign
from app.scraping import config as labeling
from app.scraping.dispatcher import auto_label_campaign
from app.scraping.functions import scrape_demo_page
from app.scraping.labels import label_demo_page
from app.services import source_catalog
from app.services.source_catalog import load_sources, CatalogError
from test_campaigns import client, create


@pytest.fixture(autouse=True)
def demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "data_mode", "demo")
    monkeypatch.setattr(scraping, "SCRAPING_SUPPORT", dict(scraping.SCRAPING_SUPPORT))
    monkeypatch.setattr(
        labeling, "AUTO_LABEL_SUPPORT", dict(labeling.AUTO_LABEL_SUPPORT)
    )


def key(source):
    return build_case_key(
        source.bank, source.product_category, source.product_name, source.language
    )


def import_one(client, bank="ING"):
    source = next(s for s in load_sources() if s.bank == bank)
    response = client.post("/api/scraping/run", json={"source_ids": [source.source_id]})
    assert response.status_code == 200, response.text
    result = response.json()["results"][0]
    assert result["status"] == "success", result
    return result["campaign_id"]


def test_contracts():
    source = load_sources()[0]
    page = ScrapedPage.model_validate(scrape_demo_page(source).model_dump())
    assert page.source == source and page.is_demo and page.success
    result = FeatureSuggestions.model_validate(
        label_demo_page(source, page).model_dump(exclude_unset=True)
    )
    assert result.values.word_count > 0 and result.values.image_count == 0
    assert label_demo_page(source, page) == label_demo_page(source, page)
    for values in (
        {"tone_formality": 6},
        {"word_count": -1},
        {"language": "EN"},
        {"average_paragraph_length": 3},
        {"word_count": True},
        {"labeling_notes": "overwrite"},
        {},
    ):
        with pytest.raises(ValidationError):
            FeatureSuggestions(values=values, is_demo=True)


def test_normalization_is_exact():
    assert build_case_key(
        " ING ", "Current Account", " Lion   Account ", "EN"
    ) == build_case_key("ing", "current_account", "lion account", "English")
    assert build_case_key(
        "ING", "Current Account", "Lion Plus", "EN"
    ) != build_case_key("ING", "Current Account", "Lion", "EN")
    assert build_case_key("ING", "Savings", "Lion", "FR") != build_case_key(
        "ING", "Current Account", "Lion", "FR"
    )
    assert build_case_key("ING", "Savings", "Lion", "FR")[-1] == "fr"
    assert build_case_key("ING", "Savings", "Lion", "Dutch")[-1] == "nl"


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
    source["language"] = " EN "
    assert SourceDefinition.model_validate(source).language == "English"


def test_registered_functions_called_and_unregistered_not_called(monkeypatch):
    source = load_sources()[0].model_copy(update={"is_example": False})
    calls = []

    def scrape(case):
        calls.append(case)
        return scrape_demo_page(case).model_copy(update={"is_demo": False})

    scraping.SCRAPING_SUPPORT[key(source)] = scrape
    page = scrape_campaign(source)
    assert calls == [source] and page.success
    unsupported = source.model_copy(update={"product_name": "Unknown product"})
    assert isinstance(scrape_campaign(unsupported), ManualRequired)
    assert calls == [source]

    def label(case, data):
        calls.append((case, data))
        return FeatureSuggestions(values={"word_count": 42}, is_demo=False)

    labeling.AUTO_LABEL_SUPPORT[key(source)] = label
    result = auto_label_campaign(source, page)
    assert result.values.word_count == 42 and calls[-1] == (source, page)
    before = len(calls)
    assert isinstance(auto_label_campaign(unsupported, page), ManualRequired)
    assert len(calls) == before


def test_catalog_is_not_dataset_and_support_is_independent(client):
    assert client.get("/api/campaigns").json() == []
    sources = client.get("/api/scraping/sources").json()["sources"]
    assert {s["bank"]: s["scraping"]["supported"] for s in sources} == {
        "ING": True,
        "KBC": True,
        "Revolut": False,
    }
    assert (
        len(
            client.get(
                "/api/scraping/sources?bank=ing&product_category=current_account"
            ).json()["sources"]
        )
        == 2
    )
    assert client.get("/api/campaigns").json() == []
    kbc_id = import_one(client, "KBC")
    support = client.get(f"/api/campaigns/{kbc_id}").json()["automation"]
    assert (
        support["scraping"]["supported"] and not support["auto_labeling"]["supported"]
    )
    result = client.post(f"/api/campaigns/{kbc_id}/auto-label")
    assert result.status_code == 200 and result.json()["status"] == "manual_required"
    assert client.get(f"/api/campaigns/{kbc_id}/suggestions").json() is None


def test_mixed_batch_success_failure_unsupported_unknown(client, monkeypatch):
    sources = [
        s.model_copy(update={"is_example": False})
        for s in load_sources()
        if s.is_example
    ]
    monkeypatch.setattr(source_catalog, "load_sources", lambda: sources)

    def fail(case):
        raise ValueError("Example source failure")

    kbc = next(s for s in sources if s.bank == "KBC")
    scraping.SCRAPING_SUPPORT[key(kbc)] = fail
    result = client.post(
        "/api/scraping/run",
        json={"source_ids": [s.source_id for s in sources] + ["unknown"]},
    ).json()["results"]
    assert [r["status"] for r in result] == [
        "success",
        "failed",
        "manual_required",
        "failed",
    ]
    assert [r["supported"] for r in result] == [True, True, False, False]
    assert len(client.get("/api/campaigns").json()) == 1
    catalog = client.get("/api/scraping/sources").json()["sources"]
    assert next(s for s in catalog if s["bank"] == "KBC")["import_status"] == "Failed"
    assert (
        next(s for s in catalog if s["bank"] == "Revolut")["import_status"] == "Ready"
    )
    scraping.SCRAPING_SUPPORT[key(kbc)] = scrape_demo_page
    assert (
        client.post("/api/scraping/run", json={"source_ids": [kbc.source_id]}).json()[
            "results"
        ][0]["status"]
        == "success"
    )


def test_duplicate_import_and_delete(client):
    campaign_id = import_one(client)
    source_id = load_sources()[0].source_id
    result = client.post(
        "/api/scraping/run", json={"source_ids": [source_id, source_id]}
    ).json()["results"]
    assert (
        len(result) == 1
        and result[0]["status"] == "existing"
        and result[0]["campaign_id"] == campaign_id
    )
    assert len(client.get("/api/campaigns").json()) == 1
    client.post(f"/api/campaigns/{campaign_id}/auto-label")
    assert client.delete(f"/api/campaigns/{campaign_id}").status_code == 204
    assert (
        client.get("/api/scraping/sources").json()["sources"][0]["import_status"]
        == "Ready"
    )
    import_one(client)


def test_existing_manual_url_is_not_overwritten(client):
    source = load_sources()[0]
    original = client.post(
        "/api/campaigns",
        json={
            "bank_name": source.bank,
            "project": source.product_category,
            "campaign_url": str(source.url) + "#section",
        },
    ).json()
    result = client.post(
        "/api/scraping/run", json={"source_ids": [source.source_id]}
    ).json()["results"][0]
    assert result["status"] == "existing" and result["campaign_id"] == original["id"]
    assert client.get(f"/api/campaigns/{original['id']}").json()["collection"] is None
    assert (
        client.post(f"/api/campaigns/{original['id']}/auto-label").json()["status"]
        == "manual_required"
    )


def test_missing_scraped_data_even_when_case_registered(client):
    source = load_sources()[0]
    campaign = client.post(
        "/api/campaigns",
        json={
            "bank_name": source.bank,
            "project": source.product_category,
            "campaign_url": str(source.url),
        },
    ).json()
    base = f"/api/campaigns/{campaign['id']}"
    client.put(
        base + "/features",
        json={"product_name": source.product_name, "language": source.language},
    )
    support = client.get(base).json()["automation"]["auto_labeling"]
    assert support["supported"] and not support["available"]
    response = client.post(base + "/auto-label").json()
    assert response["status"] == "manual_required" and response["supported"]
    assert client.post("/api/campaigns/999/auto-label").status_code == 404


def test_import_suggest_review_complete_compare(client):
    base = f"/api/campaigns/{import_one(client)}"
    assert client.get(base).json()["automation"]["auto_labeling"]["available"]
    proposal = client.post(base + "/auto-label").json()
    assert proposal["is_demo"] and not proposal["reviewed"]
    assert client.get(base).json()["has_suggestions"]
    assert client.get(base + "/features").json()["features"]["source"] == "automatic"
    assert (
        client.get("/api/compare?product_category=current_account").json()["pages"][0][
            "features"
        ]
        is not None
    )
    values = {**proposal["values"], "tone_formality": 5, "tone_friendliness": None}
    reviewed = client.post(
        base + "/suggestions/review",
        json={"token": proposal["token"], "values": values},
    )
    assert reviewed.status_code == 200, reviewed.text
    data = reviewed.json()
    assert (
        data["labeling_status"] == "In Progress"
        and data["features"]["source"] == "manual_override"
    )
    assert (
        data["features"]["tone_formality"] == 5
        and data["features"]["tone_friendliness"] is None
    )
    assert not client.get(base).json()["has_suggestions"]
    assert (
        client.post(
            base + "/features/complete", json={"confirm_incomplete": True}
        ).json()["labeling_status"]
        == "Completed"
    )
    page = client.get("/api/compare?product_category=current_account").json()["pages"][
        0
    ]
    assert (
        page["features"]["tone_formality"] == 5 and page["features"]["image_count"] == 0
    )
    assert page["labeling_status"] == "Completed"
    assert (
        client.post(
            base + "/suggestions/review",
            json={"token": proposal["token"], "values": values},
        ).status_code
        == 409
    )


def test_manual_values_survive_generation_and_stale_review(client):
    base = f"/api/campaigns/{import_one(client)}"
    client.put(
        base + "/features", json={"word_count": 999, "labeling_notes": "Keep my notes"}
    )
    client.post(base + "/features/complete", json={"confirm_incomplete": True})
    before = client.get(base + "/features").json()["features"]
    proposal = client.post(base + "/auto-label").json()
    assert client.get(base + "/features").json()["features"] == before
    client.put(base + "/features", json={"word_count": 1000})
    assert (
        client.post(
            base + "/suggestions/review",
            json={"token": proposal["token"], "values": proposal["values"]},
        ).status_code
        == 409
    )
    assert client.get(base + "/features").json()["features"]["word_count"] == 1000


def test_changed_metadata_changes_support(client):
    base = f"/api/campaigns/{import_one(client)}"
    for values in (
        {"product_name": "Different product"},
        {"product_name": "ING example current account", "language": "French"},
    ):
        client.put(base + "/features", json=values)
        assert not client.get(base).json()["automation"]["auto_labeling"]["supported"]
        assert client.post(base + "/auto-label").json()["status"] == "manual_required"


def test_replaced_proposal_token_rejected(client):
    base = f"/api/campaigns/{import_one(client)}"
    old = client.post(base + "/auto-label").json()
    new = client.post(base + "/auto-label").json()
    assert old["token"] != new["token"]
    assert (
        client.post(
            base + "/suggestions/review",
            json={"token": old["token"], "values": old["values"]},
        ).status_code
        == 409
    )


def test_invalid_function_output_isolated(client, monkeypatch):
    sources = [
        s.model_copy(update={"is_example": False})
        for s in load_sources()
        if s.is_example
    ]
    monkeypatch.setattr(source_catalog, "load_sources", lambda: sources)
    source = sources[0]

    def invalid(case):
        return scrape_demo_page(case).model_copy(
            update={"is_demo": False, "headings": "invalid"}
        )

    scraping.SCRAPING_SUPPORT[key(source)] = invalid
    result = client.post(
        "/api/scraping/run", json={"source_ids": [source.source_id]}
    ).json()
    assert result["results"][0]["status"] == "failed"
    assert client.get("/api/campaigns").json() == []
    scraping.SCRAPING_SUPPORT[key(source)] = scrape_demo_page
    campaign_id = import_one(client)

    def invalid_label(case, page):
        result = label_demo_page(case, page)
        result.values.tone_formality = 99
        return result

    labeling.AUTO_LABEL_SUPPORT[key(source)] = invalid_label
    assert client.post(f"/api/campaigns/{campaign_id}/auto-label").status_code == 422
    assert client.get(f"/api/campaigns/{campaign_id}/suggestions").json() is None


def test_demo_functions_block_real_database(client, monkeypatch):
    campaign_id = import_one(client)
    proposal = client.post(f"/api/campaigns/{campaign_id}/auto-label").json()
    monkeypatch.setattr(settings, "data_mode", "real")
    result = client.post(
        "/api/scraping/run",
        json={
            "source_ids": [
                s.source_id for s in load_sources() if s.bank in {"KBC", "Revolut"}
            ]
        },
    ).json()["results"]
    assert [r["status"] for r in result] == ["failed", "manual_required"]
    assert (
        client.post(f"/api/campaigns/{campaign_id}/auto-label").json()["status"]
        == "manual_required"
    )
    assert (
        client.post(
            f"/api/campaigns/{campaign_id}/suggestions/review",
            json={"token": proposal["token"], "values": proposal["values"]},
        ).status_code
        == 409
    )


def test_changed_url_blocks_extraction(client):
    base = f"/api/campaigns/{import_one(client)}"
    client.put(
        base,
        json={
            "bank_name": "ING",
            "project": "current_account",
            "campaign_url": "https://example.com/changed",
        },
    )
    support = client.get(base).json()["automation"]["auto_labeling"]
    assert support["supported"] and not support["available"]
    assert client.post(base + "/auto-label").json()["status"] == "manual_required"


def test_migration_matches_models(client):
    from alembic import command
    from alembic.config import Config

    command.check(Config("alembic.ini"))


def test_recapture_preserves_campaign_and_records_history(client):
    campaign_id = import_one(client)
    source = next(s for s in load_sources() if s.bank == "ING")
    client.put(
        f"/api/campaigns/{campaign_id}/features",
        json={"word_count": 999, "labeling_notes": "Keep reviewed labels"},
    )
    before = client.get(f"/api/campaigns/{campaign_id}/features").json()["features"]
    history_url = f"/api/scraping/campaigns/{campaign_id}/captures"
    first = client.get(history_url).json()
    assert len(first) == 1
    response = client.post(
        "/api/scraping/run", json={"source_ids": [source.source_id], "recapture": True}
    )
    result = response.json()["results"][0]
    assert result["status"] == "success"
    assert result["campaign_id"] == campaign_id
    history = client.get(history_url).json()
    assert len(history) == 2
    assert len({row["id"] for row in history}) == 2
    assert next(row for row in history if row["id"] == first[0]["id"]) == first[0]
    assert (
        client.get(f"/api/campaigns/{campaign_id}/features").json()["features"]
        == before
    )
    assert (
        client.get(
            f"/api/scraping/captures/{first[0]['id']}/screenshot.png"
        ).status_code
        == 404
    )


def test_failed_recapture_keeps_previous_evidence(client, monkeypatch):
    campaign_id = import_one(client)
    source = next(s for s in load_sources() if s.bank == "ING")
    history_url = f"/api/scraping/campaigns/{campaign_id}/captures"
    before = client.get(history_url).json()

    def fail(source):
        raise ValueError("Capture unavailable")

    monkeypatch.setattr("app.services.collection.scrape_campaign", fail)
    result = client.post(
        "/api/scraping/run", json={"source_ids": [source.source_id], "recapture": True}
    ).json()["results"][0]
    assert result["status"] == "failed"
    assert client.get(history_url).json() == before


def test_collected_content_available_in_campaign_detail(client):
    campaign_id = import_one(client)
    response = client.get(f"/api/scraping/campaigns/{campaign_id}/content")
    assert response.status_code == 200
    page = response.json()
    assert page["text"] and page["paragraphs"]
    assert page["source"]["bank"] == "ING"
    assert (
        client.get(f"/api/campaigns/{campaign_id}/features").json()["labeling_status"]
        == "In Progress"
    )
    manual = create(client)
    assert client.get(f"/api/scraping/campaigns/{manual['id']}/content").json() is None
    assert client.get("/api/scraping/campaigns/999999/content").status_code == 404


def test_scrape_label_failure_rolls_back_campaign(client, monkeypatch):
    def fail(*args):
        raise ValueError("Extraction failed")

    monkeypatch.setattr("app.services.collection.auto_label_campaign", fail)
    source = next(s for s in load_sources() if s.bank == "ING")
    result = client.post(
        "/api/scraping/run", json={"source_ids": [source.source_id]}
    ).json()["results"][0]
    assert result["status"] == "failed"
    assert client.get("/api/campaigns").json() == []


def test_scrape_demo_labels_available_without_second_action(client):
    campaign_id = import_one(client)
    data = client.get(f"/api/campaigns/{campaign_id}/features").json()
    assert data["labeling_status"] == "In Progress"
    assert data["features"]["source"] == "automatic"
    assert data["features"]["tone_formality"] == 3
    assert data["features"]["word_count"] > 0
    assert client.get(f"/api/campaigns/{campaign_id}/suggestions").json() is None
