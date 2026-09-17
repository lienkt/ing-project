# Scraping Engine Handoff

## Purpose

Convert one catalog source into a typed page snapshot. The service handles imports, duplicates, failures, and database writes. React and Compare do not depend on the algorithm.

## Contract

- Input: `SourceDefinition` in [contracts.py](contracts.py): stable ID, bank, bank type, country, product, category key, language, page type, HTTP(S) URL, example flag.
- Output: `ScrapedPage`: unchanged source, title/text, string lists for headings/paragraphs/images/buttons/links/sections, string metadata, timestamp, success, demo flag, warnings/error.
- `images` contains descriptions or URLs, not binaries. Return `success=False` with an error, or raise an exception, for failure. One source failure does not cancel the batch.
- Return the exact source identity; the service revalidates the result before writing.

## Current implementation

[demo_engine.py](demo_engine.py) → `DemoScrapingEngine` returns synthetic content without fetching a URL. It can write only to `DATA_MODE=demo`.

Existing `scrape_text_features_ing.py` and `scrape_text_features_bel.py` are independent experimental scripts. They are preserved and are **not** called by this workflow. Empty legacy parser/cleaner/scraper/schema files are also unchanged.

## Plug in the real engine

1. Add `app/scraping/real_engine.py` with `RealScrapingEngine`:

   ```python
   from app.scraping.contracts import SourceDefinition, ScrapedPage

   class RealScrapingEngine:
       name = "real"
       is_demo = False

       def scrape(self, source: SourceDefinition) -> ScrapedPage:
           # Implement collection and return the documented contract.
           raise NotImplementedError
   ```

2. In [engine.py](engine.py), add a `settings.scraping_engine == "real"` branch to `get_scraping_engine()` returning this class. Keep the demo branch for offline tests.
3. Set `SCRAPING_ENGINE=real` in `backend/.env`; restart the backend.
4. Replace example catalog entries with verified sources. The real engine cannot import entries marked `is_example=true`.

Do not modify API routes, import services, React, CampaignFeature, or Compare. Use finite network timeouts; requests currently run synchronously, at most 50 source IDs per batch.

## Tests

From `backend/`, with `.venv` activated:

```bash
env -u TEST_DATABASE_URL python -m pytest tests/test_collection.py -q
```

Tests cover typed output, malformed catalogs, partial failure, duplicate imports, invalid engine output, and review/Compare integration. Add fixture-based tests for your implementation, returning `ScrapedPage` through the same boundary. Do not make the regular suite depend on live bank websites.

See [collection workflow](../../../docs/collection-workflow.md) for persistence and limitations.
