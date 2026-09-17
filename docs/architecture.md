# Application Architecture

[Documentation index](README.md)

```text
React pages → typed API clients → FastAPI routes → services → SQLAlchemy → PostgreSQL
                                  Pydantic validates input and output
```

## Project map

| Location | Responsibility |
| --- | --- |
| `frontend/src/main.tsx` | Layout, navigation, routes, database mode indicator |
| `frontend/src/pages/` | Dataset, creation, labeling, comparison, and catalog screens |
| `frontend/src/api/` | Typed API clients and shared feature definitions |
| `frontend/src/components/` | Forms, workflow navigation, comparison tables/charts/findings |
| `backend/app/api/` | HTTP endpoints and database session injection |
| `backend/app/schemas/` | Request and response validation |
| `backend/app/services/` | Business rules and persistence operations |
| `backend/app/scraping/` | Source-to-page contract and replaceable engine |
| `backend/app/feature_extraction/` | Page-to-suggestions contract and replaceable engine |
| `backend/app/models/` | SQLAlchemy table mappings and relationships |
| `backend/app/core/config.py` | Environment and real/demo connection selection |
| `backend/app/database/session.py` | Engine and per-request sessions |
| `backend/alembic/versions/` | Ordered database schema migrations |
| `backend/data/` | Catalog defaults and synthetic demo fixtures |
| `backend/scripts/` | Catalog seeding and demo setup |

## Where to change campaign fields

Schemas define API input/output; models define database storage. A request passes from its route to a service, which validates business rules and saves through the database session.

| Change | File under `backend/` |
| --- | --- |
| Input validation or response fields | `app/schemas/campaign.py` |
| Create/update behavior | `app/services/campaigns.py` |
| Endpoint or HTTP method | `app/api/campaigns.py` |
| Stored columns | `app/models/campaign.py` plus a new migration |

For new stored fields, update all affected layers, the frontend API type, and the form together.

## Data relationships

A campaign stores the bank name, category key (`project`), source URL, and timestamps. It can have one details record, one optional evaluation, and one current feature-labeling record. Deleting a campaign removes those related records.

The bank catalog supplies name suggestions; the category catalog supplies validated category keys. Product names belong to campaign labeling, not to the category catalog. Legacy details/evaluation status and framework labeling status are separate concepts.

## Related guides

- [Database operations](database-guide.md): migrations and catalog seeding.
- [API reference](api-reference.md): endpoint contracts.
- [Labeling](feature-framework.md) and [comparison](comparison.md): UI behavior.

See [collection architecture and engine handoff](collection-workflow.md) for import snapshots and pending suggestions, which remain separate from CampaignFeature.
