# Presentation speaker notes

English deck · 15 slides · Suggested duration: 10–12 minutes plus demo.

## 1. Banking campaigns comparator

Introduce the team. This is a research POC for comparing communication, not a production marketing platform. The deck assesses the current repository against the two stakeholder briefs.

Evidence: Project review · 24 September 2026

## 2. The brief asks for evidence, not a bank ranking

The stakeholder presentation illustrates differences in imagery, text and layout. These are starting hypotheses, not findings produced by our app. The use case explicitly says this is not a modelling exercise. Our scope is public product pages; we do not measure campaign conversion or CTR.

Evidence: ING presentation pp. 19–22; use-case: Objective, MVP, Expected Outputs

## 3. The research workflow is implemented

Implemented evidence: scraping/page_scrapers.py, capture.py, schemas/features.py, api/features.py, services/compare.py and frontend Compare.tsx. Partial: broad bank/language coverage and visual automation. Not established: ING positioning and validated recommendations. Do not claim a POC automatically proves business impact.

Evidence: Use-case: Feature Extraction, Expected Outputs; code evidence in presentation notes

## 4. One workspace for the research team

These are current UI counts, not a market sample claim. Completed status can include acknowledged missing fields. The screenshot documents application state and should not be presented as audited source authenticity or complete research coverage.

Evidence: Local Dataset UI captured 24 September 2026; frontend/src/pages/Dashboard.tsx

## 5. From browser evidence to reviewed comparisons

Read left to right. React calls FastAPI; services coordinate persistence and scraping. Playwright collects public pages. PostgreSQL stores records and feature values; screenshot and DOM files are stored separately. Comparison reads saved features; it does not rerun extraction.

Evidence: frontend/src; backend/app/{api,services,models,scraping}; docker-compose.yml

## 6. Three actions, chosen by source state

Sources come from UI additions or configured JSON imported into user_sources on list load. For a first capture, supported sources offer Scrape & Auto-label; unsupported sources offer Capture page. After a successful capture both paths offer only Capture only. Failed first attempts retain the original action. Recapture preserves labels.

Evidence: scraping/dispatcher.py; scraping_config.py; services/collection.py; pages/Scraping.tsx

## 7. Capture the page before analysing it

Capture evidence is saved before destructive text cleanup. Each capture is a historical record. Generic capture works without creating automatic labels. Dynamic pages, banners and hidden content can still affect coverage. Source URL and timestamps enable traceability; database and artifacts must be backed up together.

Evidence: scraping/capture.py; page_scrapers.py; message_scraper.py; components/CaptureViewer.tsx

## 8. 68 fields across 8 analytical sections

Counts are derived from the current frontend feature definitions. The UI also has a ninth group for additional campaign observations. Having fields available does not mean all are automatically populated. Most visual/design fields require manual annotation.

Evidence: frontend/src/api/features.ts; backend/app/schemas/features.py; pages/Label.tsx

## 9. Measurements and heuristics produce a draft

Supported cases share code but coverage is explicitly registered. Message scoring requires at least 50 words. Keyword-based scores need language and product calibration. CTA uses visible candidates, keyword/class rules, deduplication and ranking. No trained AI model is used. Six CTA fields are persisted via the existing feature schema.

Evidence: feature_labels.py; message_analysis.py; message_analysis_config.py; cta_analysis.py

## 10. Keep the analyst in control

Show the product details screen. Explain the difference between automatic provenance and review status. Completion may acknowledge missing fields, so it is not a promise of 100 percent completeness. Recapture updates evidence without overwriting reviewed labels.

Evidence: pages/Label.tsx; api/features.py; components/FeatureControls.tsx

## 11. Compare recorded page characteristics

Observations describe ranges or equal scores in the selected sample. They are deterministic summaries, not AI insights. Missing values stay missing and higher values do not necessarily mean better. There are no bank averages or effectiveness measurements. Screenshot selection is illustrative and may include drafts.

Evidence: services/compare.py; ComparisonChart.tsx; ComparisonFindings.tsx; ComparisonTable.tsx

## 12. Useful POC; validation is still essential

The last completed backend run during implementation reported 192 passed; it was not rerun for this presentation. Tests cover implementation, not accuracy of bank labels. Sitemap discovery reads robots.txt for sitemap locations; that is not evidence that every fetch enforces robots rules. Site permission review remains a team responsibility.

Evidence: tests/test_cta.py; test_source_workflow.py; test_message_integration.py; crawling/crawling.py

## 13. What ING can use — and what comes next

Do not invent a conclusion such as ING being more rational than competitors. Next choose a defensible matched sample, double-review labels, show a few concrete differences with screenshots and then formulate improvement hypotheses. Testing those hypotheses would be separate work.

Evidence: Use-case: Expected Outputs, Goal; ING presentation pp. 21–22

## 14. Show the full loop in three minutes

Suggested team split: presenter 1 covers problem and scope; presenter 2 architecture and pipeline; presenter 3 framework, automation and review; presenter 4 comparison, limitations and next steps. Adapt to team size. Use a previously captured product to avoid waiting for external sites during the demo.

Evidence: Demo uses existing records; no live scraping dependency required

## 15. Evidence behind this presentation

Some narrative documentation in the repository is outdated; implementation checks and current UI were prioritised. No external market research or database content changes were performed for this deck. Screenshots are local, dated observations. Fonts follow frontend CSS and may substitute if unavailable on the receiving computer.

Evidence: Repository review and local screenshots · 24 September 2026