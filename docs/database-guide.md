# Database guide

The app uses one PostgreSQL database, selected by `DATABASE_URL` in `backend/.env`.
The database name does not classify its records. Preserve the database containing
your current campaigns when changing configuration.

## Local PostgreSQL

From the project root:

```bash
docker compose up -d --wait db
docker compose ps
```

Docker stores PostgreSQL data in the `campaign_data` volume. Do not remove this volume
if you need to keep the records.

## Schema updates

From `backend/`, with the virtual environment activated:

```bash
alembic current
alembic heads
alembic upgrade head
alembic check
```

The schema starts from one baseline: `0001_initial_schema.py` (revision
`initial_schema`). It creates all current tables, constraints and indexes, plus
initial bank and product-category options. It does not seed campaigns or captures.

This baseline is for an **empty database**. Databases using the retired
`0001`–`0009` chain cannot run this new chain directly. Keep any required backup,
create a new empty database, point `DATABASE_URL` to it, and run `alembic upgrade head`.
Do not use `alembic stamp` as a substitute for creating or validating the schema.
Restart the backend after changing the schema or connection settings.

## Storage

- Database: campaigns, labels, observations, evaluations, source imports and capture history.
- `user_sources`: sources added through the Scraping screen.
- `deleted_sources`: configured sources removed from the active list.
- `backend/data/sources/*.json`: configured source definitions.
- `backend/data/captures/`: screenshot and DOM artifacts; older subfolders remain readable.

## Backup and restore

Replace `YOUR_DATABASE` with the database name in `DATABASE_URL`:

```bash
docker compose exec -T db pg_dump -U postgres -Fc YOUR_DATABASE > research.dump
```

Also copy `backend/data/captures/`. A database backup alone does not include browser files.
Restore into a new, empty database first and verify the records before switching the app.

```bash
docker compose exec -T db createdb -U postgres restored_research
docker compose exec -T db pg_restore -U postgres -d restored_research < research.dump
```

## Tests

Tests use temporary SQLite databases by default. If `TEST_DATABASE_URL` is set, it must
point to a disposable test database: the fixture upgrades and downgrades its schema.
Never use a database containing research records for tests.
