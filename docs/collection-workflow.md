# Collection and Auto Labeling

[Documentation index](README.md)

```text
Source information → scraping/config.py → matching function or manual work
Imported campaign + page → auto_labeling/config.py → matching function or manual labeling
Suggestions → human review → existing CampaignFeature → Compare
```

## What is supported?

These two files are the only support lists:

- [SCRAPING_SUPPORT](../backend/app/scraping/config.py)
- [AUTO_LABEL_SUPPORT](../backend/app/auto_labeling/config.py)

Each `config.py` contains only the support list; `dispatcher.py` checks it and calls the function. Both lists use `(bank, category, product, language)` keys. Case and whitespace are normalized; category underscores match spaces; EN/English, NL/Dutch, FR/French are equivalent. Other differences do not match. There is no fallback or fuzzy matching.

Only finished functions belong in the support lists. Current explicit demo cases:

| Case                                                             | Scraping       | Auto Label                  |
| ---------------------------------------------------------------- | -------------- | --------------------------- |
| ING / Current Account / ING example current account / EN         | Demo supported | Demo supported after import |
| KBC / Current Account / KBC example current account / EN         | Demo supported | Manual only                 |
| Revolut / Current Account / Revolut example current account / EN | Manual only    | Manual only                 |

Demo cases run only in the demo database. No real algorithms are registered. The old `SCRAPING_ENGINE` and `FEATURE_EXTRACTION_ENGINE` environment settings are no longer used.

## Use the screens

1. Open **Tools → Scraping** and check **Automation** for each source.
2. Select sources and click **Scrape Selected**. Each returns imported, existing, failed, or manual required independently. Unsupported cases do not call a function or create a campaign.
3. Open Dataset. Backend support flags determine whether **Auto Label** is available. Otherwise use **Label Manually**. For manual collection, inspect the source yourself and use Settings → Add campaign; saving a URL alone does not create a scraped snapshot.
4. Auto Label creates suggestions, never final labels. **Review suggestions** opens the existing form. Keep, edit, or clear values, then explicitly save the review.
5. Complete labeling using the existing completion action. Compare continues reading CampaignFeature, never pending suggestions.

Completed rows retain the existing compact presentation. Imported status alone does not imply auto-label support. A registered labeling case also needs valid scraped data matching the campaign URL.

## Input and storage

Shared types live in `app/schemas/automation.py`. Before import, catalog entries supply the four values and have no campaign ID. For Dataset campaigns, bank/category come from the campaign; product/language come from saved features, falling back to imported source metadata when unset. Missing metadata cannot match a registered case.

No schema migration is required for this simplification. Existing tables remain:

- `source_imports`: latest import attempt, source identity, page snapshot, provenance, error, campaign link.
- `feature_proposals`: latest suggestions, review state, token, and baseline for detecting stale reviews.

Duplicate imports preserve existing records. Generation never changes saved labels. Existing pending proposals remain reviewable even if their case is no longer registered; they do not establish current automation support. Existing demo fixtures and edits remain intact.

## Limits

Batches are synchronous, up to 50 IDs. No rescrape UI, bulk Auto Label, or per-field provenance history. Review edits require an explicit save; reload resets unsaved review edits. Existing manual drafts remain visible in Compare as before.

## Developer handoff

Implement a function, test it, then add its key to config:

- [Scraping functions](../backend/app/scraping/README.md)
- [Auto-label functions](../backend/app/auto_labeling/README.md)
- [API reference](api-reference.md#collection-and-suggestions)
