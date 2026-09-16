# Comparison Methodology

[Documentation index](README.md)

## Sample selection

A comparison contains pages from one product category. Select individual pages or all pages from a bank. At least two selected pages are needed to explore the comparison; a chart also needs two recorded values for its selected scale.

Each page remains a separate record, including multiple pages from the same bank. There are no bank averages. Drafts and unlabeled pages may be selected; the interface identifies incomplete labels, mixed languages, and missing context.

## Reading results

| View | Meaning |
| --- | --- |
| Observations | Deterministic ranges or equal values for six semantic scales, with contributing page values, source links, and coverage |
| Chart | One of the 17 descriptive scales, shown as 1–5 bars; a higher value is not necessarily better |
| Detailed tables | Seven analytical sections with a column per selected page; metadata supplies context |

Observations cover text density, tone formality, emotional versus rational messaging, feature versus benefit focus, visual intensity, and CTA prominence. They describe only the selected sample; they do not measure effectiveness or recommend changes.

The page initially shows up to three observations, with a control to reveal the rest. Detailed table sections start collapsed.

## Missing values

Missing fields stay null and display as **—**. Zero counts and **No** are recorded values, not missing data. Missing chart observations are omitted rather than converted to zero. Findings report coverage so partial records remain visible in interpretation.

## Refresh and limitations

Selection changes recompute views locally from the last category response. Reopening the page or changing category fetches data again. Selection is not persisted on refresh, and other browsers' edits are not synchronized live.

The team must choose a comparable sample and apply consistent labeling. There is no stale-edit conflict detection; coordinate who labels each page.

## Implementation

- `backend/app/{api,schemas,services}/compare.py`: category-scoped retrieval and response contract.
- `frontend/src/pages/Compare.tsx`: selection and presentation.
- `frontend/src/components/ComparisonTable.tsx`, `ComparisonChart.tsx`, and `ComparisonFindings.tsx`: result views.
- `frontend/src/api/features.ts`: shared field and scale meanings.

See [API filters and responses](api-reference.md#comparison) and [feature framework](feature-framework.md).
