# Scraping: Add a Supported Case

Open [config.py](config.py). `SCRAPING_SUPPORT` is the complete list of supported cases. Missing combination = manual scraping required. No default scraper runs.

## Two steps

1. Implement and test `scrape_ing_current_account_lion_en(campaign)` in [functions.py](functions.py), or another clearly named function in that file.
2. Import it in `config.py` and add:

   ```python
   SCRAPING_SUPPORT = {
       # Keep other finished entries here.
       build_case_key(
           "ING", "Current Account", "ING Lion Account", "EN"
       ): scrape_ing_current_account_lion_en,
   }
   ```

Do not register the current TODO function until it works. Restart the backend after editing config. No API, UI, database, or router changes are needed.

## Function contract

- Input: `SourceDefinition` from [automation.py](../schemas/automation.py). It includes bank, category, product, language, URL, source ID, and optional `campaign_id` (None before import).
- Output: `ScrapedPage` from the same file. Keep `source` unchanged; return collected text/lists, timestamp, `is_demo=False`, and success/error information.
- No database writes. The import service stores the snapshot and creates the campaign.
- Raise an exception or return `success=False` for collection failure. The batch continues.

Keys ignore case, repeated whitespace, category underscores versus spaces, and EN/English, NL/Dutch, FR/French spelling. They never guess products.

## Current support

Only the exact ING and KBC **example current account / EN** cases are registered, using `scrape_demo_page`. These are synthetic and require the demo database. Revolut is manual-only. Real source entries must have verified URLs and `is_example=false`.

Your existing `scrape_text_features_ing.py` and `scrape_text_features_bel.py` remain independent experiments. Nothing imports or executes them automatically.

## Tests

From `backend/`, with `.venv` active:

```bash
env -u TEST_DATABASE_URL python -m pytest tests/test_collection.py -q
```

Add fixture-based tests for your function before registering it. See [workflow](../../../docs/collection-workflow.md).

`config.py` owns the case list; `dispatcher.py` checks support and calls the matching function; `functions.py` holds the algorithms.
