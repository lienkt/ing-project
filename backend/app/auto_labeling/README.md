# Auto Labeling: Add a Supported Case

Open [config.py](config.py). `AUTO_LABEL_SUPPORT` lists available labeling functions independently of scraping support.

## Two steps

1. Implement and test `label_ing_current_account_lion_en(campaign, scraped_data)` in [functions.py](functions.py).
2. Import it in `config.py` and add:

   ```python
   AUTO_LABEL_SUPPORT = {
       # Keep other finished entries here.
       build_case_key(
           "ING", "Current Account", "ING Lion Account", "EN"
       ): label_ing_current_account_lion_en,
   }
   ```

Keep unfinished functions out of config. Restart the backend after changes. No API, frontend, migration, or Compare changes are needed.

## Function contract

Types live in [automation.py](../schemas/automation.py):

- `campaign`: `CampaignInformation` with campaign ID, current bank/category/product/language, and URL.
- `scraped_data`: validated `ScrapedPage` stored during import.
- Return `FeatureSuggestions(values=FeatureInput(...), is_demo=False)` with optional warnings.

Use existing feature names, enums, scales, and counts. Omit unknown values. Do not return the derived average, analyst notes, or status fields. Do not write final features or mark Completed.

The dispatcher checks the exact normalized case. Unregistered cases return `manual_required`. Registered cases also need a successful, valid page snapshot for the current URL. Missing or stale data does not invoke the algorithm.

## Current support and review

Only **ING / Current Account / ING example current account / EN** is registered as a demo case. KBC scraping support does not imply KBC labeling support. Demo functions require the demo database.

The existing review form handles proposals. Explicit review saves retain In Progress until the user completes labeling. Existing manual values are not overwritten by generation; stale reviews are rejected. Provenance remains record-level.

## Tests

From `backend/`, with `.venv` active:

```bash
env -u TEST_DATABASE_URL python -m pytest tests/test_collection.py -q
```

Test your function with saved page fixtures and `FeatureSuggestions` validation before registering it.

`config.py` owns the case list; `dispatcher.py` checks support and calls the function; `functions.py` holds the algorithms.
