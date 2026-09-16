# Development Checks

[Documentation index](README.md) · [Installation](../README.md)

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
