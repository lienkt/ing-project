# Banking campaigns comparator — Backend

FastAPI with synchronous SQLAlchemy sessions, Pydantic validation, PostgreSQL, and Alembic migrations.

## Structure

- `app/main.py`: application, CORS, health endpoint.
- `app/api/campaigns.py`: HTTP routes and injected database sessions.
- `app/schemas/campaign.py`: request validation and response schemas.
- `app/models/campaign.py`: campaign, detail, and evaluation mappings.
- `app/services/campaigns.py`: persistence and manual evaluation operations.
- `app/database/session.py`: engine, base metadata, per-request sessions.
- `app/core/config.py`: environment settings.
- `alembic/`: versioned database schema.
- `tests/`: API workflow, validation, status, filtering, and migration tests.

## How the campaign API works

The campaign API separates HTTP requests, data validation, business logic, and database storage into layers:

| Layer | File | Responsibility |
| --- | --- | --- |
| Application | [app/main.py](app/main.py) | Creates the FastAPI app and registers its routers. |
| Routes | [app/api/campaigns.py](app/api/campaigns.py) | Defines URLs and HTTP methods, receives validated input, and calls services. |
| Schemas | [app/schemas/campaign.py](app/schemas/campaign.py) | Defines accepted request fields, validation rules, and response fields using Pydantic. |
| Services | [app/services/campaigns.py](app/services/campaigns.py) | Checks business rules and creates, reads, or updates records. |
| Models | [app/models/campaign.py](app/models/campaign.py) | Maps Python classes to database tables and relationships using SQLAlchemy. |
| Database session | [app/database/session.py](app/database/session.py) | Provides the connection engine and database session used by each request. |

### Schemas versus models

**Schemas define what the API accepts and returns. Models define how data is stored.**

- `CampaignCreate`: input for creating a campaign or updating its basic information (`bank_name`, `project`, `campaign_url`).
- `DetailsInput`: optional campaign content, such as headline, main message, and notes.
- `EvaluationInput`: five required scores and optional evaluation notes.
- `CampaignRead` and `EvaluationRead`: fields returned in API responses.
- `Campaign`, `CampaignDetails`, and `Evaluation`: database models mapped to the `campaigns`, `campaign_details`, and `evaluations` tables.

For example, the schema checks that `bank_name` contains 1–120 characters, while the model maps it to a database column. The service checks that the selected project exists in the project catalog.

### Example: creating a campaign

```text
Frontend sends POST /api/campaigns with JSON
    ↓
CampaignCreate validates the request fields
    ↓
The route calls create_campaign(db, data)
    ↓
The service checks the project and creates a Campaign model
    ↓
The database session saves and refreshes the record
    ↓
CampaignRead defines the response fields
    ↓
Frontend receives campaign JSON with HTTP 201 Created
```

The frontend sends this request through `createCampaign()` in [frontend/src/api/campaigns.ts](../frontend/src/api/campaigns.ts).

### Where to change basic campaign information

- **Accepted fields or validation:** edit `CampaignCreate` in `app/schemas/campaign.py`.
- **Response fields:** edit `CampaignRead` in the same schema file.
- **Creation or update behavior:** edit `create_campaign()` or `update_basic()` in `app/services/campaigns.py`.
- **URLs or HTTP methods:** edit `app/api/campaigns.py`.
- **Stored fields:** edit `Campaign` in `app/models/campaign.py` and create an Alembic migration for the database change.
- **Frontend input:** update `CampaignInput` in `frontend/src/api/campaigns.ts` and the form that collects those values.

When adding a new stored basic-info field, update the request schema, model, migration, service assignments, response schema, and frontend together.

## Start

Start PostgreSQL with `docker compose up -d --wait` from the repository root, then:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API documentation: http://localhost:8000/docs. Health: `GET /health` (process liveness, not database readiness).

## Environment

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/campaign_db` | Database connection; plain `postgresql://` is also accepted |
| `CORS_ORIGINS` | Localhost and 127.0.0.1 on ports 5173 and 5174 | JSON list of allowed frontend origins |

Run commands from `backend/` so `.env` and migration paths resolve. If Vite uses a different hostname or port, add its exact origin to `CORS_ORIGINS`.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/campaigns` | Create basic record; returns campaign, HTTP 201 |
| GET | `/api/campaigns` | Newest first; optional `bank_name` (case-insensitive exact match), `project` |
| GET | `/api/campaigns/{id}` | Campaign including details, evaluation, and status |
| PUT | `/api/campaigns/{id}` | Update bank, project, and source URL; preserves details and evaluation |
| PUT | `/api/campaigns/{id}/details` | Add/update provided fields; omitted fields preserved, null/blank clears |
| POST | `/api/campaigns/{id}/evaluation` | Create/update manual evaluation; returns evaluation, HTTP 200 |
| DELETE | `/api/campaigns/{id}` | Delete campaign, details, and evaluation; HTTP 204 |

Unknown records return 404; invalid inputs return 422. Basic creation requires a nonblank bank name, a supported project, and an HTTP(S) URL. Detail observations validate dropdown values and lengths. All five scores are required integer values from 1–5; the server never infers or averages scores.

```json
{"bank_name":"KBC","project":"credit_card","campaign_url":"https://example.com/credit-card"}
```

```json
{"clarity_score":4,"visual_score":5,"benefit_score":3,"cta_score":4,"overall_score":4,"evaluation_notes":"Clear communication and strong visuals."}
```

## Models and extension points

- `campaigns`: ID, bank name, product category, source URL, creation/update timestamps.
- `campaign_details`: optional one-to-one communication content and observations.
- `evaluations`: optional one-to-one manual evaluation, five scores with database check constraints, notes, source, timestamps.

Project options are stored in the `projects` table and validated during campaign creation and editing. The `banks` table supplies reusable bank suggestions. Migration 0002 seeds the original options and imports options from existing campaigns. Status is computed: evaluation exists → Evaluated; any nonempty observation → Details Added; otherwise Basic Info. Updating details or evaluations updates the parent timestamp.

The evaluation service is isolated and stores `source="manual"`. Future AI support can add evaluation metadata or change the one-per-campaign constraint to keep multiple evaluations; no AI code is present now.

## Migrations and tests

```bash
alembic upgrade head
alembic check
alembic revision --autogenerate -m "describe schema change"
python -m pytest -q
```

Review generated migrations before applying them. `alembic downgrade base` removes application tables and data; use only on disposable databases.

Tests apply the initial migration to temporary SQLite databases and reverse it afterward. To exercise PostgreSQL, create a dedicated empty database and run:

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/campaign_test python -m pytest -q
```

Never point `TEST_DATABASE_URL` at a database containing needed campaign data.

## Bank and project options

`GET /api/banks` and `GET /api/projects` list saved options. `POST /api/banks` and `POST /api/projects` accept `{"name":"New name"}` and return the saved option (201). Duplicate names return 409; invalid names return 422. Project names generate a stable key of up to 40 lowercase English letters, digits, and underscores. Run `alembic upgrade head` when updating an existing installation.

## Edit and delete

- `PUT /api/campaigns/{id}` edits basic information; existing detail and evaluation endpoints remain editable.
- `DELETE /api/campaigns/{id}` permanently deletes the campaign, its details, and evaluation (204).
- `PUT /api/banks/{id}` and `PUT /api/projects/{key}` accept `{"name":"New name"}`. Renames update linked campaign references and their update timestamps in the same transaction. A project rename generates a new key; use the key returned in the response for subsequent requests.
- `DELETE /api/banks/{id}` and `DELETE /api/projects/{key}` remove unused options (204). In-use options return 409; reassign or delete the linked campaigns first.
- Missing records return 404, duplicate names return 409, invalid input returns 422.

No additional migration is required for these management operations.
