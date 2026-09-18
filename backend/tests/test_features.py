import pytest
from sqlalchemy import select, func
from app.models.features import CampaignFeature
from test_campaigns import client, create


def test_feature_lifecycle(client):
    campaign = create(client)
    path = f"/api/campaigns/{campaign['id']}/features"
    empty = client.get(path).json()
    assert empty["features"] is None
    assert empty["labeling_status"] == "Not Started"
    assert empty["progress"] == 0
    saved = client.put(
        path, json={"word_count": 0, "has_hero_image": False, "text_density": 3}
    ).json()
    assert saved["labeling_status"] == "In Progress"
    assert saved["progress"] == 4
    assert saved["features"]["has_hero_image"] is False
    created_at = saved["features"]["created_at"]
    updated = client.put(path, json={"text_density": 4}).json()
    assert updated["features"]["word_count"] == 0
    assert updated["features"]["created_at"] == created_at
    assert client.get(path).json()["features"]["text_density"] == 4
    assert client.post(path + "/complete", json={}).status_code == 422
    completed = client.post(path + "/complete", json={"confirm_incomplete": True})
    assert completed.status_code == 200
    assert completed.json()["labeling_status"] == "Completed"
    listed = client.get("/api/campaigns").json()[0]
    assert listed["labeling_status"] == "Completed"
    assert listed["labeling_updated_at"]
    edited = client.put(path, json={"text_density": None}).json()
    assert edited["labeling_status"] == "In Progress"
    assert edited["features"]["text_density"] is None
    assert edited["features"]["word_count"] == 0
    from app.database.session import get_db
    from app.main import app

    generator = app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        assert db.scalar(select(func.count()).select_from(CampaignFeature)) == 1
    finally:
        generator.close()
    assert client.delete(f"/api/campaigns/{campaign['id']}").status_code == 204
    assert client.get(path).status_code == 404


SCALE_FIELDS = [
    c.name.removeprefix("ck_cf_")
    for c in CampaignFeature.__table__.constraints
    if c.name and "BETWEEN 1 AND 5" in str(c.sqltext)
]
COUNT_FIELDS = [
    c.name.removeprefix("ck_cf_")
    for c in CampaignFeature.__table__.constraints
    if c.name and ">= 0" in str(c.sqltext)
]


@pytest.mark.parametrize("field", SCALE_FIELDS)
@pytest.mark.parametrize("value", [0, 6, 1.5, True, "3"])
def test_invalid_scales(client, field, value):
    campaign_id = create(client)["id"]
    assert (
        client.put(
            f"/api/campaigns/{campaign_id}/features", json={field: value}
        ).status_code
        == 422
    )


@pytest.mark.parametrize("field", COUNT_FIELDS)
def test_negative_counts(client, field):
    campaign_id = create(client)["id"]
    assert (
        client.put(
            f"/api/campaigns/{campaign_id}/features", json={field: -1}
        ).status_code
        == 422
    )


def test_empty_completion_and_invalid_choices(client):
    campaign_id = create(client)["id"]
    path = f"/api/campaigns/{campaign_id}/features"
    assert (
        client.post(path + "/complete", json={"confirm_incomplete": True}).status_code
        == 422
    )
    assert client.put(path, json={"text_style": "Invalid"}).status_code == 422
    assert client.put(path, json={"labeling_status": "Completed"}).status_code == 422
    assert client.put(path, json={"has_hero_image": "false"}).status_code == 422
    assert client.put(path, json={"labeling_notes": "Only notes"}).status_code == 200
    assert (
        client.post(path + "/complete", json={"confirm_incomplete": True}).status_code
        == 422
    )
    assert client.put("/api/campaigns/999999/features", json={}).status_code == 404


def test_extended_metadata_and_derived_average(client):
    campaign = create(client)
    path = f"/api/campaigns/{campaign['id']}/features"
    payload = {
        "bank_type": "Traditional",
        "product_name": "ING Lion Account",
        "language": "Dutch",
        "capture_date": "2026-09-15",
        "headline_length": 6,
        "word_count": 100,
        "paragraph_count": 8,
    }
    response = client.put(path, json=payload)
    assert response.status_code == 200
    features = client.get(path).json()["features"]
    for key, value in payload.items():
        assert features[key] == value
    assert features["average_paragraph_length"] == 12.5
    assert (
        client.put(path, json={"word_count": 0}).json()["features"][
            "average_paragraph_length"
        ]
        == 0
    )
    assert (
        client.put(path, json={"paragraph_count": 0}).json()["features"][
            "average_paragraph_length"
        ]
        is None
    )
    assert (
        client.put(path, json={"word_count": None, "paragraph_count": 4}).json()[
            "features"
        ]["average_paragraph_length"]
        is None
    )
    assert (
        client.put(path, json={"headline_length": None}).json()["features"][
            "headline_length"
        ]
        is None
    )
    for invalid in (
        {"bank_type": "Unknown"},
        {"language": "German"},
        {"capture_date": "2026-02-30"},
        {"headline_length": -1},
        {"average_paragraph_length": 50},
    ):
        assert client.put(path, json=invalid).status_code == 422
    assert client.get(path).json()["campaign"]["bank_name"] == campaign["bank_name"]
