# Banking Campaign Comparator

Compare how banks communicate and present similar products, not which bank or
product is financially better. Workflow: source → capture → Dataset → Label
(human review) → Compare → insights.

## Architecture and entry points

- `frontend/src/`: React + TypeScript + Vite; pages, components, typed API clients.
- `backend/app/`: FastAPI/Pydantic routes and schemas, services, SQLAlchemy models.
- PostgreSQL is the application database; Alembic owns schema migrations.
- `backend/app/scraping/`: Playwright/Chromium capture, extraction, rule-based labels.
- Read relevant code and [development checks](docs/development.md) before editing.

## Commands and authoritative references

- Setup: [local installation](README.md#local-setup); backend development tools:
  `backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt`.
- Develop: from `backend/`, `.venv/bin/uvicorn app.main:app --reload`; from the root,
  `npm --prefix frontend run dev`.
- Verify: `./scripts/verify.sh` (the same command runs in pull-request CI).
- Consult [architecture](docs/architecture.md), [API contracts](docs/api-reference.md),
  [database and migrations](docs/database-guide.md), [label definitions](docs/labeling-field-reference.md),
  [scraper registration](backend/app/scraping/README.md), and
  [authentication setup](docs/keycloak-setup.md). [Documentation index](docs/README.md).

## Invariants

- Generic public-page capture is independent of specialized automatic labeling.
  It saves evidence and may create an unlabeled Dataset entry; never infer support
  from a bank name or URL alone.
- `scraping_config.AUTO_SUPPORT` and `dispatcher.py` gate specialized handlers by
  the exact `(bank, product category, product name, language)` key produced by
  `schemas/automation.py:build_case_key`. Only its existing normalization applies;
  no fuzzy matching, registry bypass, fake handlers, or per-bank stubs.
- Dedicated ING handling and cases in `backend/data/sources/messages.json` must
  remain supported. Catalog membership alone does not register a specialized case.
- Preserve capture history, recapture, screenshots, `dom.json`, and shadow-root
  evidence. Failed recapture must retain previous saved evidence.
- Capture-only and recapture must preserve labels and status. Automatic suggestions
  must not overwrite manual edits, completed labels, or analyst notes. Preserve
  provenance (`manual`, `automatic`, `manual_override`) and stale-review protection.
- Use deterministic extraction for measured fields. Unknown values stay missing;
  zero and false are real observations. Never fabricate semantic/subjective labels
  or silently change keyword rules, scoring, scales, or Compare behavior.
- Preserve API compatibility, Dataset → Label → Compare, and existing database/UI
  modes. Inspect current implementation rather than assuming old docs are current.
- Validate API inputs and handler outputs through `backend/app/schemas/`; shared
  `Schema` forbids unknown fields. Preserve strict feature counts/booleans and 1–5
  scales; suggestions reject empty observations and analyst notes. Do not bypass
  dispatcher revalidation with `model_construct` or unchecked dictionaries.
- Protect every `/api/` route with `core/auth.py:authorize` and add its exact
  method/route template to `backend/config/permissions.json`. With auth enabled,
  RS256 access tokens require issuer, audience, expiry and Bearer type; unknown
  roles/endpoints are denied and admin has no implicit bypass. The backend is the
  authority; frontend visibility is not access control. Auth-disabled local mode
  grants all configured permissions; `/health` is public. Policy changes require
  process restart because the validated policy is cached.

## Working rules and definition of done

1. Inspect the relevant implementation and tests; reuse existing helpers.
2. Make the smallest maintainable change; avoid unrelated rewrites/dependencies.
3. Add targeted regression tests for changed behavior, using existing fixtures.
4. Run `./scripts/verify.sh`; fix introduced failures and rerun after changes.
   It runs backend tests, TypeScript/build, and configured formatting checks.
   There is currently no frontend test runner or standalone lint command.
5. Report changed files, test evidence, and remaining failures, distinguishing
   pre-existing failures. Code alone is not completion; disclose unverified paths.

Install prerequisites using [development checks](docs/development.md). Tests use
throwaway SQLite by default. `TEST_DATABASE_URL`, if set, must identify a disposable
PostgreSQL database: tests migrate and downgrade it. Never use research/production
DBs, reset stored data, or run live bank captures as routine verification.
