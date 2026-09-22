# Banking campaigns comparator

Save bank webpages, label their communication, and compare similar products.
All application records use one PostgreSQL database, selected by `DATABASE_URL`.

## First-time installation

Follow these steps in order. Commands use macOS/Linux terminals. To use the same
research data as a teammate, obtain their database backup and capture files and
check out the same code version before starting.

### 1. Install the required tools

- **Docker Desktop:** open it and wait until Docker is running. PostgreSQL runs inside Docker; no separate PostgreSQL installation is needed.
- **Python 3.11 or newer**.
- **Node.js 22.12 or newer in the 22.x series**, including npm.

Check them in a terminal:

```bash
docker --version
docker compose version
python3 --version
node --version
npm --version
```

### 2. Start the database

Open a terminal in the project root: the folder containing this README and `docker-compose.yml`.

```bash
docker compose up -d --wait db
docker compose ps
```

Wait until `db` is healthy. This starts PostgreSQL 17 on port 5432 and creates
`campaign_db` on the first initialization. Data survives container restarts.

### 3. Install the backend

In the same terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

For a new installation, copy the example configuration:

```bash
cp .env.example .env
```

If `.env` already exists, keep it and review its settings instead. The database
name must match the database you will create or restore in the next step:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_db
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

Run backend commands from `backend/` so the app reads this `.env`. Use
`python -m pip` and `python -m uvicorn` with the same activated environment.

### 4. Prepare your data — choose one option

#### Option A: Start with an empty database

From `backend/`, with `.venv` activated and `DATABASE_URL` pointing to an empty database:

```bash
python -m alembic upgrade head
```

This creates all current tables and initial bank/category options. It does not
create campaigns, labels, or captures. Add sources through the Scraping screen.

#### Option B: Restore a teammate's data

A full database backup includes tables and research records. Screenshots and DOM
files are separate. Obtain `research.dump` and `captures.tar.gz` from your teammate.

In a terminal at the **project root**, place both files there and run these commands
once, using a new database name:

```bash
docker compose exec -T db createdb -U postgres team_research

docker compose exec -T db pg_restore \
  -U postgres --no-owner --no-privileges --exit-on-error \
  -d team_research < research.dump

tar -xzf captures.tar.gz
```

The archive should contain `backend/data/captures/`, preserving its subfolders.
Set this connection in `backend/.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/team_research
```

Do not run Option A or seed commands for this restore: the full backup already
contains the schema and data. Do not restore repeatedly into populated tables.
If any restore command fails, resolve the error before starting the app.

Verify the restored records:

```bash
docker compose exec -T db psql -U postgres -d team_research \
  -c "SELECT current_database(); SELECT COUNT(*) FROM campaigns;"
```

A restored database is a snapshot; later changes on a teammate's machine do not
sync automatically. Backups from the retired migration chain require the schema
review described under **Updating an existing installation** before future migrations.

### 5. Start the backend

From `backend/`, with `.venv` activated:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Leave this terminal running. Open **http://localhost:8000/docs** to inspect and
try API requests. `GET /api/campaigns` should return the available campaigns.

### 6. Install and start the frontend

Open a **second terminal in the project root**:

```bash
cd frontend
npm ci
```

For a new installation only:

```bash
cp .env.example .env
```

Ensure `frontend/.env` contains:

```dotenv
VITE_API_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Leave this terminal running. Open **http://127.0.0.1:5173**, or the URL printed by
Vite. If it uses another port, add that origin to backend `CORS_ORIGINS` and restart
the backend.

## Run the app next time

Do not repeat installation, migration initialization, or restore. Open Docker Desktop,
then use two terminals.

**Terminal 1 — from the project root:**

```bash
docker compose up -d --wait db
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — from the project root:**

```bash
cd frontend
npm run dev
```

Stop each app with `Ctrl+C`. To stop PostgreSQL, run `docker compose stop db` from
the project root. `docker compose down -v` deletes the stored database volume.

## App workflow

1. **Scraping:** add a product source with bank, product, category, language, and URL. Configured JSON sources are imported into the source list when it loads.
2. **First capture:** supported sources offer **Scrape & Auto-label**; other sources offer **Capture page**, without automatic labels.
3. **Recapture:** after a successful capture, **Capture only** saves new evidence in history and preserves existing labels.
4. **Dataset and Labeling:** open a product to inspect evidence, review automatic drafts, fill missing fields, and complete labeling.
5. **Compare:** select pages within the same product category to compare their recorded features.
6. **Settings:** manage bank and product-category options.

Unknown automatic fields remain unset. Review automatic drafts before completing
labeling. See the [scraping flow diagram](backend/app/scraping/README.md) for the
source lifecycle and file responsibilities.

## Share your research data

Use the same code version on both machines. Stop backend writes while exporting
so the database and capture files represent the same snapshot.

From the project root, replace `YOUR_DATABASE` with the name in your backend
`DATABASE_URL`:

```bash
docker compose exec -T db pg_dump \
  -U postgres -Fc YOUR_DATABASE > research.dump

tar -czf captures.tar.gz backend/data/captures
```

Share both files through your team's agreed storage. Do not share `.env` or `.venv`.
The database stores records and capture history; `backend/data/captures/` stores
screenshots and DOM artifacts. A database name alone does not describe its contents.

## Updating an existing installation

Pull the agreed code version, install updated dependencies with
`python -m pip install -r requirements.txt` in the backend environment and `npm ci`
in `frontend/`, then restart the servers. Keep your existing `.env` files.

The migration history was consolidated into `initial_schema`. This baseline is
for empty databases. A restored database with retired revisions `0001`–`0009`
cannot run the new chain directly. Do not rerun the initial migration over its
tables or blindly stamp its revision. Preserve a backup and validate schema
compatibility before reconciling migration history. See the
[database guide](docs/database-guide.md).

For databases already using the new baseline, apply subsequent migrations from
`backend/` before restarting:

```bash
python -m alembic upgrade head
```

## If setup fails

| Problem | Action |
| --- | --- |
| Cannot connect to Docker | Open Docker Desktop and wait for it to start. |
| Port 5432 is occupied | Stop the conflicting service or configure another host port and update `DATABASE_URL`. |
| Missing Python module | Activate the correct environment and run `python -m pip install -r requirements.txt` from `backend/`. |
| `vite: command not found` | Run `npm ci --include=dev` in `frontend/`, then `npm run dev`. |
| Backend cannot connect to PostgreSQL | Check `docker compose ps` and `DATABASE_URL` in `backend/.env`. |
| Wrong data or an empty Dataset | Check the database name, query its campaign count, and restart the backend after changing `.env`. |
| Table already exists during restore | Restore into a new empty database; do not initialize its tables first. |
| Missing table or column | Confirm the code version and database schema match. An old backend may request removed columns such as `is_demo`. |
| CORS error | Include the exact frontend origin in `CORS_ORIGINS` and restart the backend. Also check backend logs for request errors. |
| Frontend cannot reach the API | Keep the backend running on port 8000 and check `VITE_API_URL`. Restart Vite after changing its `.env`. |
| Screenshots or DOM are missing | Restore `backend/data/captures/` alongside the matching database backup, keeping its folder structure. |

## Development tools and checks

Run backend tests from `backend/`:

```bash
.venv/bin/python -m pytest -q
```

Tests use temporary SQLite databases by default. Never point `TEST_DATABASE_URL`
at a database containing research records.

Check the frontend build from `frontend/`:

```bash
npm run build
```

From the project root, install the Python formatter:

```bash
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

Prettier is included in the frontend dependencies. In VS Code, install the
workspace's recommended **Prettier** and **Ruff** extensions to format on save.
See [formatting commands](docs/development.md#formatting).

## Further documentation

- [Database guide](docs/database-guide.md): configuration, migrations, backup, and restore.
- [Scraping flow](backend/app/scraping/README.md): diagram, source actions, and implementation files.
- [Architecture](docs/architecture.md): application structure and responsibilities.
- [Labeling field reference](docs/labeling-field-reference.md): fields and scale definitions.
- [Comparison](docs/comparison.md): page selection and interpretation.
- [API reference](docs/api-reference.md): endpoints and contracts.
- [Development checks](docs/development.md): tests, formatting, and manual verification.
- [Documentation index](docs/README.md): all project guides.
