"""Validation boundaries without a database or live captures."""

import pytest
from pydantic import ValidationError

from app.schemas.automation import FeatureSuggestions
from app.schemas.campaign import CampaignCreate, DetailsInput, EvaluationInput


@pytest.mark.parametrize(
    "schema,payload",
    [
        (
            CampaignCreate,
            {
                "bank_name": "ING",
                "project": "current_account",
                "campaign_url": "https://example.com/account",
                "status": "Evaluated",
            },
        ),
        (DetailsInput, {"source": "automatic"}),
        (
            EvaluationInput,
            {
                "clarity_score": 3,
                "visual_score": 3,
                "benefit_score": 3,
                "cta_score": 3,
                "overall_score": 3,
                "source": "automatic",
            },
        ),
        (FeatureSuggestions, {"values": {"word_count": 0, "source": "manual"}}),
    ],
)
def test_inputs_reject_server_owned_fields(schema, payload):
    with pytest.raises(ValidationError) as error:
        schema.model_validate(payload)
    assert any(item["type"] == "extra_forbidden" for item in error.value.errors())


@pytest.mark.parametrize("values", [{"word_count": 0}, {"has_hero_image": False}])
def test_zero_and_false_are_valid_suggestions(values):
    suggestions = FeatureSuggestions.model_validate({"values": values})
    assert suggestions.values.model_dump(exclude_unset=True) == values


def test_null_only_suggestions_are_rejected():
    with pytest.raises(ValidationError, match="non-null suggestion"):
        FeatureSuggestions.model_validate({"values": {"word_count": None}})
