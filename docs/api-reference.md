# API Reference

[Documentation index](README.md)

Run the backend and open http://localhost:8000/docs for the complete interactive schemas.

## System

- `GET /health`: process liveness, not database readiness.
- `GET /api/environment`: selected `data_mode` only; no connection credentials.

## Campaigns

| Method | Path                             | Behavior                                                                     |
| ------ | -------------------------------- | ---------------------------------------------------------------------------- |
| POST   | `/api/campaigns`                 | Create basic record; returns campaign, HTTP 201                              |
| GET    | `/api/campaigns`                 | Newest first; optional `bank_name` (case-insensitive exact match), `project` |
| GET    | `/api/campaigns/{id}`            | Campaign including details, evaluation, and status                           |
| PUT    | `/api/campaigns/{id}`            | Update bank, project, and source URL; preserves details and evaluation       |
| PUT    | `/api/campaigns/{id}/details`    | Add/update provided fields; omitted fields preserved, null/blank clears      |
| POST   | `/api/campaigns/{id}/evaluation` | Create/update manual evaluation; returns evaluation, HTTP 200                |
| DELETE | `/api/campaigns/{id}`            | Delete campaign, details, evaluation, and feature labels; HTTP 204           |

Unknown records return 404; invalid inputs return 422. Basic creation requires a nonblank bank name, a supported project, and an HTTP(S) URL. Detail observations validate dropdown values and lengths. All five scores are required integer values from 1–5; the server never infers or averages scores.

```json
{
  "bank_name": "KBC",
  "project": "credit_card",
  "campaign_url": "https://example.com/credit-card"
}
```

```json
{
  "clarity_score": 4,
  "visual_score": 5,
  "benefit_score": 3,
  "cta_score": 4,
  "overall_score": 4,
  "evaluation_notes": "Clear communication and strong visuals."
}
```

## Catalog management

`GET /api/banks` and `GET /api/projects` list options. `POST` to either path accepts `{"name":"New name"}` and returns the created option (201). Duplicate names return 409. Category names generate keys of up to 40 lowercase English letters, digits, and underscores.

- `PUT /api/campaigns/{id}` edits basic information; existing detail and evaluation endpoints remain editable.
- `DELETE /api/campaigns/{id}` permanently deletes the campaign, its details, evaluation, and feature labels (204).
- `PUT /api/banks/{id}` and `PUT /api/projects/{key}` accept `{"name":"New name"}`. Renames update linked campaign references and their update timestamps in the same transaction. A project rename generates a new key; use the key returned in the response for subsequent requests.
- `DELETE /api/banks/{id}` and `DELETE /api/projects/{key}` remove unused options (204). In-use options return 409; reassign or delete the linked campaigns first.
- Missing records return 404, duplicate names return 409, invalid input returns 422.

No additional migration is required for these management operations.

## Feature labeling

| Method | Endpoint                                | Behavior                                                                                                                                                                                |
| ------ | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/api/campaigns/{id}/features`          | Campaign context, feature record, status, progress, and missing field names. Existing campaign without labels returns HTTP 200 with `features: null`, `Not Started`, and zero progress. |
| PUT    | `/api/campaigns/{id}/features`          | Create or partially update one record. Omitted fields are preserved; explicit null clears a value. Sets `In Progress`.                                                                  |
| POST   | `/api/campaigns/{id}/features/complete` | Accepts `{}` for a fully populated record, or `{"confirm_incomplete": true}` to acknowledge omissions. Sets `Completed`.                                                                |

All three responses include `campaign`, `features`, `labeling_status`, `progress`, and `missing_fields`. Unknown campaigns return 404. Invalid scales, negative counts, invalid enum values, and unconfirmed incomplete completion return 422. Clients cannot set status or provenance through the draft payload. Campaign list/detail responses also include `labeling_status`, `labeling_progress`, and `labeling_updated_at`.

## Comparison

`GET /api/compare` reads existing campaigns and their current feature records. No migration or sample-data seed is needed for comparison.

Required query parameter: `product_category` (the existing project key). Optional repeated parameters: `campaign_ids` and `bank_names`.

```text
/api/compare?product_category=current_account
/api/compare?product_category=current_account&campaign_ids=1&campaign_ids=2
/api/compare?product_category=current_account&bank_names=ING&bank_names=KBC
```

Filters combine with AND; bank names match case-insensitively. IDs cannot bypass the category constraint. Unknown or nonmatching IDs/categories return an empty `pages` array. Omitting category returns 422. Omitting ID/bank filters returns all pages in the category.

The response contains `product_category` and `pages`. Each page includes `campaign_id`, `bank_name`, `bank_type`, `product_name`, `product_category`, `page_url`, `language`, `capture_date`, `labeling_status`, and the existing `FeatureRead` object as `features`. A page without labeling has `features: null` and `Not Started` status. Missing fields remain null; zero/false remain actual values. Multiple pages from a bank remain separate records; there is no implicit bank aggregation.

See [feature framework](feature-framework.md) and [comparison methodology](comparison.md) for interpretation.

## Collection and suggestions

| Method | Endpoint                                 | Result                                                                                                                            |
| ------ | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/api/scraping/sources`                  | Catalog with per-source `scraping` support; optional bank/category filters                                                        |
| POST   | `/api/scraping/run`                      | `{ "source_ids": ["ing-example-current-account-en"] }`; 1–50 IDs with independent success/existing/failed/manual_required results |
| POST   | `/api/campaigns/{id}/auto-label`         | Stored proposal, or `{ "status": "manual_required", "supported": false, "message": "..." }`                                       |
| GET    | `/api/campaigns/{id}/suggestions`        | Latest proposal or null                                                                                                           |
| POST   | `/api/campaigns/{id}/suggestions/review` | `{ "token": "returned-token", "values": { "word_count": 42 } }`; explicit reviewed save as In Progress                            |

Campaign responses include `automation.scraping` and `automation.auto_labeling`. Each support object contains `supported` (registered case), `available` (can run now), `is_demo`, and `message`. A registered label function without valid scraped input returns `manual_required` with `supported: true`; it is not called.

Unsupported cases are normal 200 responses, not engine failures. Batch results distinguish `manual_required` from `failed`. Unknown campaigns return 404; stale review saves return 409; invalid requests or label-function results return 422. Malformed catalog files return 500 with validation details.

Review values use the existing partial FeatureInput contract. Omitted final fields are preserved; null clears them. Completion still uses the existing endpoint. See [workflow](collection-workflow.md) for matching, demo safety, and review behavior.
