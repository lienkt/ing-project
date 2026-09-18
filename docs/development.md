# Development Checks

[Documentation index](README.md) · [Installation](../README.md)

## Formatting

Use Prettier for frontend code, JSON, YAML, and Markdown; use Ruff for Python. Both use an 88-character target line width. Tool setup is in the [root README](../README.md#development-tools-optional).

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

Use demo or disposable records:

- Create a campaign; find and open it in Dataset.
- Save labels, change sections, and refresh to verify persistence.
- Complete labeling; edit and save again to verify the return to In Progress.
- Compare two pages; check saved values, missing cells, chart scales, and source links.
- Try empty selection, one page, and unlabeled pages.
- Check catalog edits, deletion, keyboard navigation, and narrow screens.
