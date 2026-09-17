# Feature Extraction Engine Handoff

## Purpose

Turn a stored page snapshot into suggestions for the existing Campaign Feature Framework. This module does not save final labels or mark campaigns Completed.

## Contract

- Input: `ScrapedPage` from [scraping/contracts.py](../scraping/contracts.py).
- Output: `FeatureSuggestions` from [contracts.py](contracts.py): `values`, `is_demo`, and `warnings`.
- `values` is a partial existing `FeatureInput`. Use its exact enum strings, integer scales 1–5, nonnegative counts, and nullable values.
- Omit unobserved fields. Never send derived `average_paragraph_length`, system/status fields, or analyst `labeling_notes`.
- Include at least one non-null observation. Invalid outputs fail validation before any proposal is saved.

## Current implementation

[demo_engine.py](demo_engine.py) → `DemoFeatureExtractionEngine` counts the synthetic snapshot and supplies three fixed example scales. It is deterministic and contains no NLP, ML, or LLM. Writes require `DATA_MODE=demo`.

## Plug in the real engine

1. Add `app/feature_extraction/real_engine.py`:

   ```python
   from app.scraping.contracts import ScrapedPage
   from app.feature_extraction.contracts import FeatureSuggestions

   class RealFeatureExtractionEngine:
       name = "real"
       is_demo = False

       def extract(self, page: ScrapedPage) -> FeatureSuggestions:
           # Return proposed values using the existing FeatureInput schema.
           raise NotImplementedError
   ```

2. Add a `settings.feature_extraction_engine == "real"` branch in [engine.py](engine.py), inside `get_feature_extraction_engine()`. Keep the demo branch.
3. Set `FEATURE_EXTRACTION_ENGINE=real` in `backend/.env`; restart the backend.

Do not modify routes, React, review persistence, or Compare. The service preserves demo provenance when the input page is synthetic, even if the extractor is real.

## Review and provenance

Proposals are stored separately. The existing form prefills empty fields while keeping manual values, and disables autosave during review. Explicit review saves to CampaignFeature as In Progress with `source=manual_override`. Existing completion rules still apply.

Only the latest proposal and its reviewed flag are retained. This is not a per-field acceptance history. Tokens and feature snapshots reject stale review saves.

## Tests

From `backend/`, with `.venv` activated:

```bash
env -u TEST_DATABASE_URL python -m pytest tests/test_collection.py -q
```

The suite verifies valid/invalid outputs, missing scraped data, no automatic completion, preservation of manual values, stale review rejection, and final values in Compare. Add fixture-based tests for the real algorithm using `FeatureSuggestions` validation.
