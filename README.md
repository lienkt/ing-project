# Banking campaigns comparator

Capture bank product pages, label their communication, and compare similar products.
All application records use one database, configured by `DATABASE_URL`.

## Local setup

Requires Docker Desktop, Python 3.11+, and Node.js 22.12+ (22.x).

Start PostgreSQL from the project root:

```bash
docker compose up -d --wait db
```

Install the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For a new installation, copy `.env.example` to `.env`. For an existing installation,
keep `.env` and ensure `DATABASE_URL` points to the database containing your records.
Do not replace it with an empty database.

```bash
python -m playwright install chromium
alembic upgrade head
python -m scripts.seed_catalog
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
# New installations only: copy .env.example to .env.
npm run dev
```

Open http://localhost:5173. API documentation: http://localhost:8000/docs.

## Workflow

1. **Scraping:** add a source, capture its page, or run supported scraping and labeling.
2. **Dataset:** open a product to inspect capture history and labels.
3. **Labeling:** review automatic drafts, add observations, then complete labeling.
4. **Compare:** select pages in the same product category.

Capture only never creates automatic labels. Recapture preserves manual and completed
labels. Screenshots and DOM files live in `backend/data/captures/`; back up this folder
alongside the database.

## Updating and testing

The migration history has been consolidated into `initial_schema` for a fresh
start. Use an empty database; existing databases on the retired migration chain
must be backed up and replaced with a new database before using this baseline.
See the [database guide](docs/database-guide.md). No reset is performed automatically.

For subsequent updates on this baseline, run `alembic upgrade head` from `backend/`
and restart the backend.

```bash
cd backend
.venv/bin/python -m pytest -q
```

```bash
cd frontend
npm run build
```

See [scraping flow](backend/app/scraping/README.md),
[database guide](docs/database-guide.md), and [API reference](docs/api-reference.md).
