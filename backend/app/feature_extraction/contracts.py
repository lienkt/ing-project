"""Suggestions reuse the existing framework, never a second analytical model."""
from pydantic import Field, model_validator
from app.schemas.campaign import Schema
from app.schemas.features import FeatureInput


class FeatureSuggestions(Schema):
    values: FeatureInput
    is_demo: bool
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def observations_only(self):
        if "labeling_notes" in self.values.model_fields_set:
            raise ValueError("Suggestions must not replace analyst notes")
        if not any(v is not None for v in self.values.model_dump(exclude_unset=True).values()):
            raise ValueError("At least one non-null suggestion is required")
        return self
