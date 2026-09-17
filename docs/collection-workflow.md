# Collection and Automatic Suggestions

[Documentation index](README.md)

```text
Source catalog → Scraping → Dataset → Auto suggestions → Human review
                                  ↘ Manual labeling ↗       ↓
                                                       Completed → Compare
```

## Try it

Use the [README setup](../README.md), with the demo database selected. Existing installations must apply migration `0005` before starting the updated app:

```bash
# From backend/, with .venv activated:
DATA_MODE=demo alembic upgrade head
```

1. Open **Tools → Scraping**.
2. Filter sources or select the three example pages. Click **Scrape Selected**.
3. Read each result, then open **Dataset**.
4. On an unfinished imported row, choose **Auto Label**, or **Review suggestions** if a proposal already exists. Completed rows show neither action. For manual labeling, open the campaign by its bank name. Import details stay out of the Dataset table; the app header still identifies demo mode.
5. Auto Label opens the existing framework. Suggested values fill empty fields; existing manual values remain. Each proposed field includes an “Auto suggested” hint. Use the proposal list to replace an existing value explicitly.
6. Keep, change, or clear values. **Save Reviewed Draft** saves In Progress; **Complete Labeling** saves the review and uses existing completion checks.
7. Compare reads the existing feature records, never the pending suggestions.

Autosave is disabled during suggestion review. Reloading before saving resets review edits. Save any recovered manual draft before entering review. Pending proposals survive reloads and can be reopened from Dataset.

## Boundaries

| Component | Owns |
| --- | --- |
| `services/source_catalog.py` | File loading, validation, filters, stable source lookup |
| `scraping/` | Source → page contract and engine selection |
| `feature_extraction/` | Page → suggestions contract and engine selection |
| `services/collection.py` | Import transactions, duplicates, proposals, human review |
| Existing feature services | Manual saves, completion, analytical values |
| Existing Compare | Feature values only; no proposal access |

## Storage and safety

Migration `0005` adds two tables without changing existing feature fields:

- `source_imports`: one latest attempt per source, unique normalized URL, optional campaign link, snapshot, engine/demo provenance, time, error. Successful imports create campaigns; failed ones do not.
- `feature_proposals`: one latest suggestion set per campaign, engine/demo flag, review state, token, and baseline for detecting edits during review.

Repeated imports return the existing campaign, including manual records with the same normalized URL. Such manual records are not given synthetic scraped data. Source ID and URL uniqueness protect concurrent imports; campaign deletion removes its import/proposal records.

Generating suggestions never edits final/manual features. Review rejects an outdated token or changed feature snapshot. Changing the source URL blocks extraction from its old snapshot. Reviewed saves use record-level `manual_override` provenance; individual accepted/edited fields are not tracked historically.

## Demo configuration

Defaults in `backend/.env.example`:

```dotenv
SCRAPING_ENGINE=demo
FEATURE_EXTRACTION_ENGINE=demo
```

Demo engines write only to `DATA_MODE=demo`. The source page, Dataset, and review screen identify synthetic data. The sample catalog uses placeholder URLs and is not evidence about the named banks.

## Limits

- Synchronous batches of up to 50 IDs; results appear when the batch finishes. No queues or live per-source progress.
- Imports skip existing campaigns; no refresh/rescrape or history UI.
- Single-campaign Auto Label only; optional bulk extraction is deferred.
- Manual drafts remain visible in Compare as before. Pending automatic suggestions are never included.
- No scraper/ML/LLM algorithm added. Existing experimental scripts remain separate.
- Review saves have stale-data protection; the legacy manual editor still has its original concurrency behavior.

## Engine handoff

- [Scraper developer](../backend/app/scraping/README.md)
- [Feature-extraction developer](../backend/app/feature_extraction/README.md)
- [API contracts](api-reference.md#collection-and-suggestions)

## Prepared demo examples

Demo setup also seeds three Current Account examples alongside the manual-labeling fixtures:

| Bank | Product | State |
| --- | --- | --- |
| ING | Auto review example — pending | Scraped; Auto Suggested; no saved feature labels yet |
| KBC | Auto review example — draft | Suggestions reviewed and edited; In Progress |
| Revolut | Auto review example — completed | Suggestions reviewed and edited; Completed with acknowledged omissions |

All three have synthetic page snapshots and proposals. Reviewed records use `manual_override` provenance. Re-running demo setup adds missing URLs without resetting your edits.
