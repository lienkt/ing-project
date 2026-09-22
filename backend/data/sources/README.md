# Source catalog

JSON files here contain configured public product pages. Each file has a `sources`
array validated by `SourceDefinition`. Keep `source_id` stable after import.

On loading Scraping Sources, missing entries are imported into `user_sources`.
The screen reads that table. Existing rows are retained, and `deleted_sources`
prevents deleted configured entries from being re-imported.

- Normal sources support generic capture without an automatic label handler.
- `messages.json` also registers the exact cases for message/tone automation.
- Dedicated handlers are registered in `app/scraping/scraping_config.py`.

Capture history and labels are stored in the database; browser artifacts are stored
under `backend/data/captures/`.
