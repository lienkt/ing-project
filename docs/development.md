# Development Checks

[Documentation index](README.md) · [Installation](../README.md)

## Agent verification

After installing frontend dependencies and backend `requirements-dev.txt`, run:

```bash
./scripts/verify.sh
```

The executable resolves the repository root itself, runs backend tests, then
TypeScript checking and the Vite production build, then Prettier and Ruff
formatting checks. It stops at the first failure with a non-zero exit code and
names the failed step. It does not install dependencies, change formatting,
start services, migrate the application database, or capture live bank pages.
There is no frontend test runner or standalone lint command configured.

Read [AGENTS.md](../AGENTS.md), inspect relevant code, implement the smallest
change, run verification, fix introduced failures, rerun, and report evidence.
Tests use disposable SQLite databases by default; never point `TEST_DATABASE_URL`
at research data. See [database test safety](database-guide.md#12-run-tests-without-affecting-research-data).

`backend/tests/test_scraping_invariants.py` checks production registry support,
exact dispatch, evidence requirements, missing counts, and both artifact writers
without network requests or database migrations. Existing integration tests cover
capture-only, history, protected labels, stale reviews, and Compare compatibility.
Browser mocks verify contracts; rendered bank pages still need human inspection.

## Formatting

Use Prettier for frontend code, JSON, YAML, and Markdown; use Ruff for Python. Both use an 88-character target line width. Install the frontend dependencies using [local setup](../README.md#local-setup); install backend development tools with `pip install -r requirements-dev.txt` from `backend/`.

From the project root:

```bash
npm --prefix frontend run format
backend/.venv/bin/ruff format backend
```

Check formatting without changing files:

```bash
npm --prefix frontend run format:check
backend/.venv/bin/ruff format --check backend
```

VS Code formats on save when the recommended extensions are installed. Keep formatting-only commits separate from behavior changes when possible so diffs remain easy to review.

## Backend tests

Use the [database testing instructions](database-guide.md#12-run-tests-without-affecting-research-data) for SQLite or disposable PostgreSQL tests. Schema checks and migration creation are covered under [migrations](database-guide.md#8-manage-migrations-when-updating-code).

## Frontend build

From the project root:

```bash
cd frontend
npm run build
npm run preview
```

Build checks TypeScript and creates `dist/`. Preview usually uses port 4173; add its exact origin to backend `CORS_ORIGINS` and restart the backend. Static hosting must serve `index.html` for application routes.

## Manual checks

For authenticated installations, first run the [Keycloak login and role checks](keycloak-setup.md#6-check-login-logout-and-permissions).

Use disposable test records:

- Create a campaign; find and open it in Dataset.
- Save labels, change sections, and refresh to verify persistence.
- Complete labeling; edit and save again to verify the return to In Progress.
- Compare two pages; check saved values, missing cells, chart scales, and source links.
- Try empty selection, one page, and unlabeled pages.
- Check catalog edits, deletion, keyboard navigation, and narrow screens.
