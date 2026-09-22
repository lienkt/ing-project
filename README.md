# Banking campaigns comparator

Save bank webpages, label their communication, and compare similar products.

## First-time installation

Follow these steps in order. This starts the app with demo data. Commands use macOS/Linux terminals.

### 1. Install the required tools

Install these tools if missing:

- **Docker Desktop:** install it, open it, and wait until Docker is running. PostgreSQL runs inside Docker; no separate PostgreSQL installation is needed.
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

Wait until `db` is healthy before continuing. This downloads PostgreSQL 17 and starts it on port 5432. Its data survives container restarts.

### 3. Install the backend

In the same terminal:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Copy `.env` only if it does not already exist. Open `backend/.env` and set these values; keep the other settings:

```dotenv
DATA_MODE=demo
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_db
DEMO_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_demo_db
```

### 4. Load demo data and start the backend

Still in `backend/`, with `.venv` activated:

```bash
python -m scripts.setup_demo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The setup command creates the demo database, creates its tables, and adds sample campaigns. Leave this terminal running. Check the API at **http://localhost:8000/docs**.

### 5. Install and start the frontend

Open a **second terminal in the project root**:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Copy `.env` only if it does not already exist. Its `VITE_API_URL` should be `http://localhost:8000`. Leave this terminal running.

### 6. Open the app

Open **http://localhost:5173**. The header should show **Demo database · Synthetic data**.

- **Dataset:** click a bank name to open a campaign and its labeling.
- **Compare:** choose **Current Account**, then select at least two labeled pages. Observations appear above the chart.
- **Settings:** add campaigns, banks, or product categories.

Demo labels are synthetic; they are for exploring the app.

## Run the app next time

Do not repeat installation or demo setup. Open Docker Desktop, then use two terminals.

**Terminal 1 — from the project root:**

```bash
docker compose up -d --wait db
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — from the project root:**

```bash
cd frontend
npm run dev
```

Open http://localhost:5173. Stop each app with `Ctrl+C`. To stop PostgreSQL, run `docker compose stop db` from the project root. Do not use `docker compose down -v`: it deletes stored databases.

## Use real data instead

Stop the backend. From `backend/`, with `.venv` activated:

```bash
DATA_MODE=real alembic upgrade head
DATA_MODE=real python -m scripts.seed_catalog
```

Set `DATA_MODE=real` in `backend/.env`, then restart the backend using the command above. The real database is separate from demo data. Use Settings → Add campaign to enter research pages.

To switch back, set `DATA_MODE=demo` and restart the backend. Existing records in both databases are preserved.

## If setup fails

| Problem                              | Action                                                                                   |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| `command not found`                  | Install the missing tool, then reopen the terminal                                       |
| Cannot connect to Docker             | Open Docker Desktop and wait for it to start                                             |
| Port 5432 is occupied                | Stop the conflicting local PostgreSQL service, or follow the existing-server guide below |
| Backend cannot connect to PostgreSQL | Check `docker compose ps` and the URLs in `backend/.env`                                 |
| Missing Python module                | Activate `backend/.venv` and install `requirements.txt`                                  |
| Frontend cannot reach the API        | Keep the backend running on port 8000; check `VITE_API_URL`                              |
| Wrong data appears                   | Check `DATA_MODE`, restart the backend, and refresh the browser                          |

## Try source import and Auto Label

In demo mode, open **Tools → Scraping**, check which sources are **Auto supported**, select sources, and click **Scrape Selected**. The ING example supports Auto Label after import; KBC requires manual labeling, and Revolut requires manual collection. Unsupported cases are reported individually. Review any generated suggestions before saving or completing labeling. Demo results are placeholders, not collected evidence.

For an existing installation, apply `DATA_MODE=demo alembic upgrade head` from `backend/` before starting the updated app. See [collection workflow](docs/collection-workflow.md) for details and developer handoff.

## Further documentation

- [Database operations](docs/database-guide.md): existing/shared PostgreSQL, migrations, backup, restore, and team data.
- [Development checks](docs/development.md): tests and frontend build.
- [Documentation index](docs/README.md): architecture, labeling reference, API, and comparison.
