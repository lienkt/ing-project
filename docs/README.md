# Documentation

Start with the [project README](../README.md) for complete local installation, demo setup, and app startup.

backend/
└── app/
├── api/
│ ├── campaigns.py
│ ├── features.py
│ └── analysis.py
│
├── models/
│ ├── campaign.py
│ └── features.py
│
├── schemas/
│ ├── campaign.py
│ └── features.py
│
├── services/
│ ├── campaigns.py
│ └── features.py
│
├── scraping/ # NEW
│ ├── **init**.py
│ ├── scraper.py
│ ├── parser.py
│ ├── cleaner.py
│ └── schemas.py
│
├── automated_labeling/ # NEW
│ ├── **init**.py
│ ├── labeler.py
│ ├── text_features.py
│ ├── visual_features.py
│ ├── rules.py
│ └── schemas.py
│
└── main.py

| Document                                                | Purpose                                                                 |
| ------------------------------------------------------- | ----------------------------------------------------------------------- |
| [Database guide](database-guide.md)                     | Existing servers, database maintenance, migrations, backup, and restore |
| [Application overview](application-overview.md)         | Terms, navigation, and scope                                            |
| [Collection workflow](collection-workflow.md) | Source catalog, scraping, automatic suggestions, and engine handoff |
| [Architecture](architecture.md)                         | File responsibilities and where to change code                          |
| [Feature framework](feature-framework.md)               | Saving, completion, and progress                                        |
| [Labeling field reference](labeling-field-reference.md) | Every field, allowed values, examples, and scale definitions            |
| [Comparison](comparison.md)                             | Selection and result interpretation                                     |
| [API reference](api-reference.md)                       | Endpoints and contracts                                                 |
| [Development checks](development.md)                    | Build and manual verification                                           |

Keep documentation in English. Update the relevant guide and link to it instead of copying instructions between files.
