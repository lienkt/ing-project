# Scraping and labeling

Select a product under Tools → Scraping and click **Scrape & Label Selected**.
One request captures its page, extracts supported fields, and saves an **In Progress**
labeling draft. Open the campaign details page to review, correct, and complete
its labels in the same page. The form includes progress, Save Draft, and Complete
Labeling. Additional campaign observations is the final labeling section, with its own
recorded-field count and Previous/Next navigation. It shares Save Draft and
Complete Labeling with the other sections.
The Campaign options menu has been removed; existing `/campaigns/:id/label`
links redirect to the combined details page.

All collection and extraction code lives in `backend/app/scraping/`:

- `config.py` registers exact supported scraping and feature-extraction cases.
- `dispatcher.py` validates source identity, availability, and demo provenance.
- `functions.py` captures page content; `labels.py` extracts draft feature values.
- `scrapping_pipeline.py` supplies shared text scoring calculations.

Every successful import fills measured text counts and source metadata. The ING
Youth Account English case also fills text style, density, and information
complexity using the existing rules. Unknown visual, CTA, and tone fields stay
unset. Synthetic demo scores are only used for registered demo cases.

The page, capture history, and draft are committed together. A failed extraction
rolls back the import. Duplicate imports are skipped unless recapture is requested.
Recapture refreshes untouched automatic drafts and preserves manually edited or
completed labels. Old pending proposals are invalidated. Unsupported scraping
cases still require manual collection.

Completion remains a human action. Compare reads saved feature drafts, so the
prefilled values are visible immediately and should be reviewed before use.

The legacy `/auto-label` and suggestion-review endpoints remain compatible with
existing clients and pending proposals, but the frontend needs no separate
label-generation action. No database migration is required for this change.
