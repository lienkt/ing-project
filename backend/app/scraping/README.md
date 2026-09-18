# Scraping

## App flow

`Scrape Selected → dispatcher.scrape_campaign → config.SCRAPING_SUPPORT → functions.scrape_ing_youth_account_en → functions.scrape_site`

The existing collection service saves the returned `ScrapedPage` snapshot and creates the campaign. No scraper writes to the database. One failed source does not stop the batch. Existing campaigns are not overwritten.

- `config.py`: exact bank/category/product/language → function mapping, browser settings, site configuration, filters and scoring vocabulary.
- `dispatcher.py`: checks registration and demo provenance, calls the function, validates its output.
- `functions.py`: synchronous app adapter, browser lifecycle, page loading, cleaning, extraction, 120-second collection timeout and snapshot conversion.
- `scrapping_pipeline.py`: standalone experimental text scoring; imports the shared scraper from `functions.py`. The app does not call this module.
- `main_scrapping.py`: optional standalone URL-file runner; the app does not call it. From `backend/`, run `python -m app.scraping.main_scrapping --file path/to/urls.txt`. It exports JSON rather than importing campaigns.

## Registered sources

The ING Youth Account English URL supplied in the original script is now in `backend/data/sources/ing.json`, mapped to `scrape_ing_youth_account_en`. Select it under Tools → Scraping after restarting the backend. This is real collection, including when using the demo database. Browser installation is documented in the [root README](../../../README.md).

The synthetic ING/KBC example sources remain separate and require demo mode. Unregistered cases remain manual-only.

To add a source, add its metadata to `backend/data/sources/*.json` and its matching `build_case_key(...)` entry to `SCRAPING_SUPPORT`. Create a dedicated entry point named `scrape_<bank>_<product>_<language>` for each real case. Validate the exact case before opening the browser, construct its own `SiteConfig`, and pass its own async extractor to `_collect_page`. The extractor owns site-specific navigation, cookie handling and selectors; it may reuse extraction helpers where verified. Do not map another product or language to the ING Youth Account function. Keep unfinished cases out of the registry. Validate extracted content for each website before relying on it.

The ING case targets `ing-feat-flexible-page` and waits for its product-header heading. Saved ING DOM confirms that the layout `<main>` only contains a slot, so using it as the extraction root misses the product content. The selector fix was checked by replaying saved open shadow roots locally. Live completeness, cookie handling and collapsed FAQ still require review.

## Output and limits

Snapshots retain headline, combined text, headings, paragraphs, bullets, tables, list count, timestamp and final URL. New fields have defaults so older snapshots still load. Storage uses the existing JSON column; no migration is needed.

HTTP errors and empty text fail collection. Scrolling is bounded. The supplied extraction rules still exclude tables from combined text, count all list containers, and remove broad header/footer/overlay selectors. Cookie barriers or error pages returning HTTP 200 may require site-specific handling. Images, buttons and links are not collected; their empty snapshot lists are not measured zero counts.

`build_features` and the nine scoring calculations are retained but are **not called by the app's scraping flow**. Real Auto Label remains manual-only until a function is connected in `auto_labeling/`. Paragraph-average semantics differ from the current app, and the scoring vocabulary supports only English/Dutch. French scoring raises an error unless explicit financial vocabulary is supplied. URL-derived identity in the standalone runner is only a guess; the app always uses source catalog metadata.

The independent `scrape_text_features_ing.py` and `scrape_text_features_bel.py` experiments remain unused by the app.

## Capture history (prototype)

Apply `alembic upgrade head` from `backend/` using the intended DATA_MODE before restarting the backend. Revision 0006 adds `page_captures`; it does not rewrite saved labels.

Tools → Scraping now offers **Capture again for existing products** and **View captures**. A successful collection adds an immutable evidence record. Recapture reuses the existing campaign, preserves saved labels, and invalidates pending suggestions based on the old evidence. Failed recapture leaves previous evidence intact. Legacy evidence is preserved when first recaptured. Demo captures remain synthetic and have no screenshot.

Real collection saves `screenshot.png` (full page, before cleanup) and `dom.json` (document HTML plus open shadow roots) under `backend/data/captures/<data_mode>/<artifact_id>/`. Back up this directory together with the database. Files are ignored by Git. Use the capture API links to view artifacts; HTML is returned as JSON rather than executed. Capture history is available at `/api/scraping/campaigns/{campaign_id}/captures`.

This is the first evidence-storage prototype, not a completed universal extractor or AI labeler. Cookie handling, product-ready checks, accordion expansion and closed shadow roots still require appropriate adapters. Capture uses the current rendered state, so cookie banners may remain and collapsed content is not shown in screenshots. Saved labels may describe an older capture; recapture does not imply they were reviewed again. AI integration, bulk background jobs, scheduled change detection, file retention/orphan cleanup and manual artifact upload remain future work. Files from a capture whose later extraction or database write fails can remain on disk; they are not listed as successful captures. Deleting a campaign removes its database history but does not yet delete its files.

ING cleanup regression: the cookie dialog adds `overlays-scroll-lock` to `<body>`. The broad overlay selector previously removed the entire body. Global cleanup now protects the document/body, and the ING adapter skips global cleanup altogether in favor of scoped product reads. The registered scraper was verified on the live page after this fix; this does not establish completeness of collapsed FAQ or remove the cookie banner from screenshots.
