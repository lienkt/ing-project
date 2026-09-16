# Database Operations Guide

[Documentation index](README.md) · [App installation and startup](../README.md)

For first-time local installation, demo setup, and app startup, follow the [project README](../README.md#first-time-installation) from start to finish. This guide covers database maintenance and other deployment cases.

## Existing or shared PostgreSQL server

Skip Docker setup. Use PostgreSQL 17 for consistency with the project. Have the administrator create a real database and a separate demo database if needed, and grant your account connection and schema/table creation rights for migrations.

Once the server is available, complete [backend installation](../README.md#3-install-the-backend). Then set your actual server, port, account, and database names in `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/REAL_DATABASE
DEMO_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DEMO_DATABASE
```

Replace placeholders; URL-encode special characters in credentials. Keep `.env` private and use the server's required TLS settings. Both URLs must refer to different databases.

For real data, follow [Use real data](../README.md#use-real-data-instead). For demo data, use the README demo setup command if your account can create databases. If the account cannot create databases, ask the administrator to create an empty demo database, then use this alternative from `backend/`:

```bash
DATA_MODE=demo alembic upgrade head
DATA_MODE=demo python -m scripts.seed_demo
```

Docker inspection/backup/restore examples later in this guide target the local container only. For an external server, use PostgreSQL client tools with that server's host, port, user, and database; do not run container commands expecting them to reach the external database. Use a password prompt or configured credential file rather than putting passwords in shell history.

## Task index

- [Switch demo/real](#4-select-the-real-or-demo-database)
- [Inspect records](#7-inspect-databases-and-tables)
- [Update schema](#8-manage-migrations-when-updating-code)
- [Back up and share](#9-back-up-data-to-share-with-the-team)
- [Restore a snapshot](#10-restore-a-shared-dataset)
- [Team workflows](#11-team-workflows)
- [Test safely](#12-run-tests-without-affecting-research-data)
- [Troubleshoot](#13-troubleshooting)

## 1. Where is the database stored?

The default local setup stores PostgreSQL 17 data in a Docker volume, not a SQLite `.db` file. External servers manage their own storage.

| Component | Purpose |
| --- | --- |
| `campaign_db` | Default real/research database |
| `campaign_demo_db` | Separate database containing synthetic demo data |
| Docker service `db` | Runs PostgreSQL for both databases |
| Docker volume `campaign_data` | Persists PostgreSQL data; the actual volume name usually includes the project prefix |
| `backend/.env` | Selects the database mode and connection URLs |
| `backend/data/demo_campaigns.json` | Input fixtures for demo seeding, not the running database |
| `backend/data/taxonomy.json` | Default bank and product-category options for seeding |
| `backend/alembic/versions/` | Versioned database schema migrations |

The volume is mounted at `/var/lib/postgresql/data` inside the container. Editing a JSON fixture does not automatically update records already stored in PostgreSQL.

## 2. Command conventions

- Run `docker compose ...` commands from the **repository root**, where `docker-compose.yml` is located.
- Run Python and Alembic commands from **`backend/`**, with the virtual environment activated.
- Docker examples use the default local PostgreSQL instance and user `postgres`. Adjust connection details when using another server.
- Shell examples target macOS/Linux.

## 3. Start and stop PostgreSQL

Use [Run the app next time](../README.md#run-the-app-next-time) for startup and shutdown commands. Inspect connection failures from the project root:

```bash
docker compose logs --tail=100 db
```

`docker compose down` preserves the named volume. Adding `-v` deletes it, including both real and demo databases.

## 4. Select the real or demo database

Follow [Use real data instead](../README.md#use-real-data-instead) to prepare and select real data or switch back to demo. The mode selects the connection for the API and Alembic; the two URLs must identify separate databases.

No frontend URL change is needed. The application header displays the database mode. While the backend is running, you can also check:

```bash
curl http://127.0.0.1:8000/api/environment
```

Example response: `{"data_mode":"demo"}`.

Shell environment variables take precedence over `.env`. For example, `DATA_MODE=real alembic current` selects the real database for that command only; it does not edit `.env` or switch an already-running backend.

## 5. Prepare the real database

Docker creates `campaign_db` only when it initializes a new volume. Changing the Compose database name later does not create a new database in an existing volume. If the configured local real database is missing, create it once from the repository root:

```bash
docker compose exec -T db createdb -U postgres campaign_db
```

Skip this command if the database already exists. Never remove the volume to fix a missing database. Continue with [Use real data instead](../README.md#use-real-data-instead) to migrate and seed it.

`seed_catalog` adds missing options from `backend/data/taxonomy.json`; it does not overwrite or delete existing entries. Historical migrations also insert initial options. To use another file:

```bash
DATA_MODE=real python -m scripts.seed_catalog --file path/to/taxonomy.json
```

Use the catalog UI/API to edit existing options. Removing a JSON entry does not remove it from PostgreSQL. Renaming or deleting an option in the UI can cause its original seed entry to be added again on the next seed run; update the JSON defaults if that is unwanted.

## 6. Prepare the demo database

First-time setup is in [README step 4](../README.md#4-load-demo-data-and-start-the-backend). It targets `DEMO_DATABASE_URL` regardless of the selected mode, creates tables, and inserts missing fixtures. It requires database-creation permission; for restricted accounts, use [an existing server](#existing-or-shared-postgresql-server).

If the demo database is already prepared and you only need to add missing fixtures:

```bash
DATA_MODE=demo python -m scripts.seed_demo
```

The script skips existing URLs, avoiding duplicates and preserving edits. It refuses to run in `real` mode.

Demo records use normal bank names such as ING and KBC, but all labels are **synthetic**, not research evidence. Fixture source URLs and capture dates do not establish that an actual page review took place.

### Legacy installations with demo records in the real database

Back up the real database first using [Backup](#9-back-up-data-to-share-with-the-team). Use this only when moving old fixtures with the `DEMO — ` prefix, before normal demo setup populates matching destination URLs:

```bash
python -m scripts.setup_demo --move-existing
```

The script identifies records using fixture URLs and the legacy bank-name prefix. It copies their data and edits to the demo database before removing the corresponding originals. Research campaigns are not moved. If a URL already exists at the destination, the script stops to prevent overwriting; inspect both records before resolving the conflict. The destination commits before source deletion; a later failure may leave both copies. Do not delete either blindly.

## 7. Inspect databases and tables

From the repository root:

```bash
# List databases:
docker compose exec db psql -U postgres -d postgres -c '\l'

# Open the real database:
docker compose exec db psql -U postgres -d campaign_db
```

Inside `psql`:

```sql
\dt
SELECT current_database();
SELECT COUNT(*) FROM campaigns;
SELECT labeling_status, COUNT(*) FROM campaign_features GROUP BY labeling_status;
SELECT version_num FROM alembic_version;
\q
```

To inspect demo data, replace `-d campaign_db` with `-d campaign_demo_db`.

Main tables: `banks`, `projects`, `campaigns`, `campaign_details`, `evaluations`, and `campaign_features`. The `alembic_version` table records the current migration revision.

**Note:** the `-d` argument to `psql`, `pg_dump`, and `pg_restore` selects a database directly. These commands do not read `DATA_MODE` from `.env`.

## 8. Manage migrations when updating code

From `backend/`:

```bash
source .venv/bin/activate
DATA_MODE=real alembic current
DATA_MODE=real alembic heads
DATA_MODE=real alembic upgrade head
DATA_MODE=real alembic check
```

- `current`: reports the revision applied to the selected database.
- `heads`: reports the latest migration revision available in the code.
- `upgrade head`: applies pending migrations.
- `check`: checks for differences between model metadata and the database schema; it does not fix them automatically.

Update the demo database separately when needed:

```bash
DATA_MODE=demo alembic upgrade head
```

When a developer changes a model:

```bash
DATA_MODE=real alembic revision --autogenerate -m "describe schema change"
```

Review the generated migration before applying it. Commit models and their migrations together. Back up research data before schema changes; create a new migration rather than editing one the team has already applied.

## 9. Back up data to share with the team

From the repository root, create a snapshot of the real database:

```bash
mkdir -p backups
backup_path="backups/campaign_real_$(date +%Y%m%d_%H%M%S).dump"
docker compose exec -T db pg_dump \
  -U postgres -d campaign_db \
  -Fc --no-owner --no-acl > "$backup_path"
```

Only share the backup if `pg_dump` finishes successfully without errors. Check that PostgreSQL can read the archive contents:

```bash
docker compose exec -T db pg_restore --list < "$backup_path"
```

This checks the archive format. Restoring into an empty database, as described below, provides a fuller recovery check.

The `.dump` file includes table definitions, data, sequences, and the migration revision. It does not include the application's complete source code or `.env` configuration.

To back up demo data, replace `-d campaign_db` with `-d campaign_demo_db` and use a filename that clearly identifies it as demo data.

Share the dump together with:

- The code version or Git commit used to produce it.
- The export date.
- Whether it contains real or demo data.
- A short description of the dataset's scope.

Use the team's shared storage. Do not commit `.env` or database dumps to the repository by default; the current Git configuration does not automatically exclude every `.dump` file. You can add `backups/` to `.git/info/exclude` to ignore local backups on your machine.

## 10. Restore a shared dataset

Use the same code version and the project's Docker PostgreSQL 17 setup. From the repository root, assuming the received file is named `campaign_real.dump`:

```bash
docker compose up -d --wait db

# Create a new database; do not run Alembic against it first:
docker compose exec -T db createdb -U postgres campaign_shared_db

# Restore both schema and data:
docker compose exec -T db pg_restore \
  -U postgres -d campaign_shared_db \
  --no-owner --no-acl --exit-on-error --single-transaction \
  < campaign_real.dump
```

If `campaign_shared_db` already exists, use a new name such as `campaign_shared_v2_db` in both commands. Do not restore a full dump over an existing dataset or a database already initialized by migrations.

Edit the recipient's `backend/.env`:

```dotenv
DATA_MODE=real
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_shared_db
```

Keep `DEMO_DATABASE_URL` pointed at a separate demo database. From `backend/`:

```bash
source .venv/bin/activate
DATA_MODE=real alembic current
DATA_MODE=real alembic upgrade head
DATA_MODE=real alembic check
```

Restart the backend. Open Dataset, a labeled campaign, and Compare to verify the restored data.

**Restoring a dump restores a snapshot; it does not merge datasets.** If two team members edit separate copies, this workflow does not automatically reconcile their changes.

## 11. Team workflows

### Share snapshots

Suitable when one person consolidates data and sends it to the team for demonstrations or analysis. Each member has a local PostgreSQL instance. Changes made after export are not synchronized automatically.

### Use a shared PostgreSQL server

Suitable when the team needs to enter and view the same data. Each backend points `DATABASE_URL` at the shared server and uses `DATA_MODE=real`. The team must configure the host, accounts, and network access separately; the local Docker setup does not automatically become an Internet-accessible shared database.

Assign campaigns to individual team members to avoid concurrent edits to the same record. The application currently does not detect conflicting saves from multiple editors.

## 12. Run tests without affecting research data

From `backend/`, with `.venv` activated, use temporary SQLite databases by default:

```bash
env -u TEST_DATABASE_URL python -m pytest -q
```

For PostgreSQL tests, create a dedicated database from the repository root:

```bash
docker compose exec -T db createdb -U postgres campaign_test_db
```

Then, from `backend/`:

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_test_db \
  python -m pytest -q
```

**Never point `TEST_DATABASE_URL` at research data, demo data you need to keep, or the team's shared database.** The test fixture runs migration downgrades and removes application tables from the test database.

## 13. Troubleshooting

| Symptom | What to check |
| --- | --- |
| Cannot connect to PostgreSQL | Check Docker, `docker compose ps`, service logs, and port 5432 |
| Demo database does not exist | Run `python -m scripts.setup_demo` from `backend/` |
| Database creation permission denied | Ask the PostgreSQL administrator to create the empty demo database and grant appropriate access |
| Old data still appears after switching mode | Restart the backend; check `/api/environment` and shell environment overrides |
| Missing tables or columns after a code update | Run `alembic upgrade head` with the correct `DATA_MODE` |
| Demo seeding is refused | Run `DATA_MODE=demo python -m scripts.seed_demo` |
| Editing JSON does not change the UI | JSON is seed input; existing records are preserved rather than synchronized |
| Restore reports existing tables | Restore into a new, empty database |
| Teammates cannot see new changes | Dumps do not synchronize; export a new snapshot or use shared PostgreSQL |

## Related documentation

- [Running the application](../README.md)
- [Backend setup](../backend/README.md)
- [Frontend setup](../frontend/README.md)
- [Documentation index](README.md)
