from sqlalchemy import select
from sqlalchemy.orm import Session
from test_campaigns import client
from test_generic_capture import add_source, fake_capture
from app.models.collection import UserSource
from app.schemas.automation import FeatureSuggestions


def source_row(client, source_id):
    return next(
        s
        for s in client.get("/api/scraping/sources").json()["sources"]
        if s["source_id"] == source_id
    )


def test_json_sources_persist_once_and_stay_deleted(client):
    from app.database import session

    first = client.get("/api/scraping/sources").json()["sources"]
    client.get("/api/scraping/sources")
    with Session(session.engine) as db:
        rows = list(db.scalars(select(UserSource)))
        assert {r.source_id for r in rows} == {s["source_id"] for s in first}
        assert len(rows) == len(first)
    source_id = first[0]["source_id"]
    assert client.delete(f"/api/scraping/sources/{source_id}").status_code == 204
    for _ in range(2):
        assert source_id not in {
            s["source_id"]
            for s in client.get("/api/scraping/sources").json()["sources"]
        }


def test_first_auto_then_capture_preserves_automatic_draft(client, monkeypatch):
    source_id = "ing-youth-account-en"
    assert not source_row(client, source_id)["has_capture"]
    monkeypatch.setattr("app.services.collection.scrape_campaign", fake_capture)
    monkeypatch.setattr(
        "app.services.collection.auto_label_campaign",
        lambda *args: FeatureSuggestions(values={"word_count": 123}),
    )
    payload = {"source_ids": [source_id], "mode": "scrape_and_label"}
    result = client.post("/api/scraping/run", json=payload).json()["results"][0]
    assert result["status"] == "success"
    cid = result["campaign_id"]
    base = f"/api/campaigns/{cid}/features"
    before = client.get(base).json()["features"]
    assert before["source"] == "automatic" and before["word_count"] == 123
    assert source_row(client, source_id)["has_capture"]

    def forbidden(*args):
        raise AssertionError("Recapture must never recalculate labels")

    monkeypatch.setattr("app.services.collection.auto_label_campaign", forbidden)
    result = client.post(
        "/api/scraping/run", json={**payload, "recapture": True}
    ).json()["results"][0]
    assert result["status"] == "success"
    assert client.get(base).json()["features"] == before
    captures = client.get(f"/api/scraping/campaigns/{cid}/captures").json()
    assert len(captures) == 2
    assert sorted(c["page"]["metadata"]["capture_mode"] for c in captures) == [
        "capture_only", "scrape_and_label"
    ]


def test_failed_first_capture_does_not_change_action(client, monkeypatch):
    source = add_source(client, monkeypatch)

    def fail(*args):
        raise ValueError("Network failed")

    monkeypatch.setattr("app.scraping.page_scrapers.capture_generic_page", fail)
    payload = {"source_ids": [source["source_id"]], "mode": "capture_only"}
    assert (
        client.post("/api/scraping/run", json=payload).json()["results"][0]["status"]
        == "failed"
    )
    assert not source_row(client, source["source_id"])["has_capture"]
    monkeypatch.setattr("app.scraping.page_scrapers.capture_generic_page", fake_capture)
    assert (
        client.post("/api/scraping/run", json=payload).json()["results"][0]["status"]
        == "success"
    )
    assert source_row(client, source["source_id"])["has_capture"]
