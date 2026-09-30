# Documentation

[Project README](../README.md) · [Install and run](../README.md#local-setup)

This is the central map of the project documentation. Choose a reading path below;
use the reference tables when you need a specific implementation detail.

## For users and reviewers

Read these in order when preparing your first comparison:

1. [Application overview](application-overview.md): understand the screens, terms and scope.
2. [Collection workflow](collection-workflow.md): add sources, capture evidence and understand automatic drafts.
3. [Labeling workflow](feature-framework.md): review, save and complete labels.
4. [Labeling field reference](labeling-field-reference.md): check field meanings, examples and scale definitions while labeling.
5. [Comparison methodology](comparison.md): select comparable pages and interpret results and missing values.

## For developers

1. Follow [local setup](../README.md#local-setup) and read the [architecture](architecture.md) to locate the code you need.
2. Use the [backend README](../backend/README.md) or [frontend README](../frontend/README.md) for component-specific entry points.
3. For collection or automation changes, read the [source catalog](../backend/data/sources/README.md), [scraping pipeline](../backend/app/scraping/README.md) and [collection workflow](collection-workflow.md).
4. Consult the [API reference](api-reference.md) for contracts and the [database guide](database-guide.md) for persistence and migrations.
5. Run the relevant [development checks](development.md) before sharing changes.

## For database maintenance

Read the [database guide](database-guide.md) before changing database configuration,
applying migrations, or backing up and restoring research data. Saved capture files
must be preserved alongside database records.

## Guides and references

| Guide | What it explains |
| --- | --- |
| [Application overview](application-overview.md) | Purpose, navigation, terms and scope |
| [Collection workflow](collection-workflow.md) | Sources, capture, automatic labels and function integration |
| [Labeling workflow](feature-framework.md) | Saving, completion and progress |
| [Labeling field reference](labeling-field-reference.md) | Fields, allowed values, examples and scales |
| [Comparison methodology](comparison.md) | Sample selection and interpretation |
| [Architecture](architecture.md) | File responsibilities and where to change code |
| [API reference](api-reference.md) | Endpoints and contracts |
| [Database guide](database-guide.md) | Database configuration, migrations, backup and restore |
| [Development checks](development.md) | Formatting, tests, builds and manual verification |

## Component READMEs

| README | When to use it |
| --- | --- |
| [Backend](../backend/README.md) | Work on FastAPI, persistence or API behavior |
| [Frontend](../frontend/README.md) | Work on React screens and comparison UI |
| [Scraping pipeline](../backend/app/scraping/README.md) | Understand capture actions, handlers and evidence storage |
| [Source catalog](../backend/data/sources/README.md) | Configure source JSON and register supported cases |

## Maintaining these docs

Keep documentation in English. Update the relevant guide and link to it instead of
copying instructions between files. Add new guides to this index and provide a link
back here so readers can continue navigating.
