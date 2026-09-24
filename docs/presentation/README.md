# Team presentation

Created on 24 September 2026 from the stakeholder PDF, use-case DOCX, current
repository implementation, and read-only screenshots of the local application.

- **Banking_Campaigns_Comparator_Team.pptx**: 15 editable slides with speaker notes.
- **Banking_Campaigns_Comparator_Preview.pdf**: companion preview generated from the same layout; portable fonts and rectangular cards may differ slightly from PowerPoint.
- **speaker-notes.md**: speaking guidance and evidence references for every slide.
- **slide-overview.png**: overview of the entire deck.
- **assets/**: actual local application screenshots.

The deck is in English and targets a 10–12 minute presentation plus a short demo.
PowerPoint uses Manrope and DM Sans, matching `frontend/src/styles.css`; install
these fonts for the closest visual match, or use PowerPoint's font substitution.

## Requirements and delivery assessment

| Brief requirement | Current delivery | Evidence | Remaining work |
| --- | --- | --- | --- |
| Focused, reproducible POC | End-to-end source, capture, label, compare flow | PDF pp. 21–22; `backend/app/services/collection.py` | Declare the final research sample and exclusions |
| Public webpage evidence | Playwright screenshots, DOM, text and capture history | `backend/app/scraping/capture.py`, `page_scrapers.py`, `message_scraper.py` | Check site permissions and capture completeness |
| Structured campaign features | 68 fields in 8 sections, plus observations | `frontend/src/api/features.ts`, `backend/app/models/features.py` | Review missing values and annotation consistency |
| Text and messaging comparison | Measured text values and heuristic message/tone drafts | `feature_labels.py`, `text_scoring.py`, `message_analysis.py` | Calibrate keywords and scales across languages/categories |
| Visual and layout comparison | Fields available for manual review | `frontend/src/api/features.ts`, `frontend/src/pages/Label.tsx` | Complete visual labels; broad visual automation is not claimed |
| CTA analysis | Six rendered-page metrics integrated with auto-labeling | `cta_analysis.py`, `cta_analysis_config.py`, `tests/test_cta.py` | Validate against human annotations; no backfill claimed |
| Consistent comparison | Category-scoped pages, feature tables, scale charts, deterministic observations | `backend/app/services/compare.py`, frontend comparison components | Match language, product and collection context |
| ING positioning and improvement ideas | App supports investigation; conclusions not established by this audit | Use-case: Expected Outputs; PDF pp. 21–22 | Build and defend conclusions from reviewed evidence |
| Collection constraints | Public URL checks in generic/message flow; sitemap discovery tooling | `public_urls.py`, `backend/app/crawling/crawling.py` | Sitemap discovery is not proof of robots-policy enforcement |
| Reusable research asset | Database records and capture artifacts | Database models and `backend/data/captures/` | Keep code, database revision and artifact backups aligned |

Scraping module paths in the table are relative to `backend/app/scraping/` unless
otherwise specified. The use-case source is
`docs/use_case_description_beCode_campaign_comparator.docx`; the stakeholder PDF is
`docs/20260914_ProjectPresentation-compressed.pdf`.

## Presentation boundaries

- The Dataset screenshot showed **19 campaigns, 2 completed and 17 awaiting completion** at capture time. These are UI counts, not a verified market sample.
- Completion may include acknowledged missing fields; it is not equivalent to complete annotation coverage.
- Comparison screenshots illustrate the interface and stored values, not validated claims about market positioning or campaign performance.
- The **192 passing backend tests** refer to the last completed implementation run in this work session history, not a new test run for the deck.
- No database records were modified to prepare this presentation.
- Some older narrative documentation is stale; current code and UI were prioritised.
