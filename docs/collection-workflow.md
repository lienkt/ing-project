# Scraping, capture, and labeling

For a fresh installation, apply `alembic upgrade head` from `backend/` to an
empty database. The initial schema includes persistent user sources, campaigns,
labels, and capture history. See the [database guide](database-guide.md) for
the requirements when replacing a database on the retired migration chain.

On Tools → Scraping, **Add source** saves bank, product name, category, language,
and public HTTP(S) URL. Bank and category use the existing Settings catalogs.
Sources are retained in the active database; configured JSON sources still appear.
Unknown bank type remains unset.

Each source uses the existing exact bank/category/product/language registry:

- **Specialized scraper available**: use **Scrape & Auto-label** when a label
  extractor is registered, or **Capture only** to skip all label creation.
- **Generic capture only**: use **Capture page**. One shared Playwright handler
  captures screenshot, DOM with open shadow roots, text, headings, paragraphs,
  bullet items and tables. No feature labels or proposals are generated.
- **Capture selected** captures evidence only for selected new sources.
- Existing products can be captured again through the row actions, adding history.

A new capture-only campaign remains Not Started. Its submitted product name and
language remain visible without fabricating a feature record. Manually edited
and completed labels are preserved. Specialized auto-label recapture may refresh
an untouched automatic draft. Previous pending proposals are invalidated when
new evidence is captured. Failed recapture preserves existing database evidence.

All capture and labeling code lives in `backend/app/scraping/`. `scraping_config.py` retains
SCRAPING_SUPPORT and AUTO_LABEL_SUPPORT. `page_scrapers.py` shares browser lifecycle
and extraction between specialized and generic capture. `feature_labels.py` and the
scoring formulas are unchanged. Generic capture does not call them.

Generic extraction is best-effort: cookie banners, navigation, collapsed content,
and site-specific layouts can affect results. Empty extracted text can still
produce a generic evidence capture with a warning.

Open View captures to inspect history, screenshots and dom.json, then manually
review labels on the campaign details page. Compare reads saved feature values;
missing values stay missing. The legacy auto-label/review endpoints remain for
compatibility.
