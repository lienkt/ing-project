# Banking campaigns comparator

A local research workspace for collecting and manually evaluating bank communication campaigns. Capture a source URL, add communication observations, and save five independently chosen scores. No scraping, AI scoring, authentication, or competitor algorithms are included.

## Architecture

React + TypeScript (Vite) → FastAPI REST API → SQLAlchemy → PostgreSQL.

The dashboard shows workflow status and filters by bank and product category. Campaign details and evaluations live in separate related tables. Alembic manages the schema; the application never creates tables on startup.

```text
.
├── backend/              # FastAPI, SQLAlchemy, schemas, services, migrations, tests
├── frontend/             # React pages, shared components, typed API client
├── docker-compose.yml   # PostgreSQL with persistent storage
└── README.md
```

## Run locally

Prerequisites: Python 3.11+, Node.js 20.19+ (or 22.12+), npm, and Docker with Compose. Run these commands from the repository root unless stated otherwise.

1. Start PostgreSQL:

   ```bash
   docker compose up -d --wait
   ```

   If Docker isn’t installed. Your Python virtual environment doesn’t include it. Install Docker Desktop:

   ```bash
   brew install --cask docker
   ```

   Then, Open Docker Desktop from Applications and wait for it to finish starting. From the repository root, retry:

   ```bash
   docker compose up -d --wait
   ```

2. Start the backend in one terminal:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   alembic upgrade head
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

3. Start the frontend in a second terminal:

   ```bash
   cd frontend
   cp .env.example .env
   npm ci
   npm run dev
   ```

4. Open **http://localhost:5173**. API docs: **http://localhost:8000/docs**.

PostgreSQL is available at localhost:5432, database `campaign_db`, user/password `postgres`/`postgres`. These credentials are for local development. If you already have PostgreSQL, create an empty database and set `DATABASE_URL` instead of using Compose. If port 5432 is occupied, adjust the Compose host port and backend environment together.

## Try the complete workflow

1. Add campaign → enter bank, product category, and HTTP(S) URL.
2. The saved record opens on its details page; a success message confirms creation.
3. Enter observations and save details; continue to evaluation.
4. Select all five scores (1–5) and save. Overall score is also selected manually.
5. Return to the dashboard. The campaign now shows **Evaluated**.

Campaigns remain available after refresh or service restart. Submitting an evaluation again updates its existing manual evaluation. Filters and text search apply to the current campaign library; an empty installation has no fabricated sample data.

## Verification

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
alembic check
```

Tests use isolated SQLite databases with real Alembic upgrades and downgrades by default. To test against PostgreSQL, supply a **dedicated empty test database** (tests remove their tables):

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_test python -m pytest -q
```

```bash
cd frontend
npm run build
```

See [backend documentation](backend/README.md) and [frontend documentation](frontend/README.md) for structure and API details. `docker compose stop` stops PostgreSQL while preserving data; `docker compose up -d --wait` resumes it.

## Implementation verification

Verified during implementation:

- 14 backend tests pass, including create/list/details/evaluation, input validation, filtering, status changes, and migration upgrade/downgrade.
- TypeScript checking and the Vite production build pass.
- FastAPI and Vite both start successfully.
- A headless Chrome check completes creation, details editing, evaluation, dashboard navigation, filtering, and persistence after refresh; no browser errors or page overflow at 390px width.
- Alembic applies to a temporary SQLite database, `alembic check` reports no model/schema differences, and PostgreSQL migration SQL generates successfully.

The implementation environment had neither Docker nor PostgreSQL installed. **Live PostgreSQL migration and workflow verification remain to be run** using the Compose instructions above. Browser verification used a temporary SQLite database, not the default PostgreSQL configuration.

### Add banks and projects

Use **Add bank** or **Add project** below **Add campaign** in the sidebar. Saved options are available when creating and editing campaigns. For an existing installation, run `alembic upgrade head` from `backend/` to create and seed the option tables while preserving campaigns.

Campaigns can be edited or deleted from the dashboard. Bank and project pages support adding, editing, and deleting options. Renames update linked campaigns. Options still in use cannot be deleted until their campaigns are reassigned or removed. Campaign deletion also removes its details and scores and asks for confirmation.
