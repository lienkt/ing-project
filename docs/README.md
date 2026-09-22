# Documentation

Start with the [project README](../README.md) for complete local installation and app startup.

## Automation code

```text
backend/app/
├── scraping/           # scraping_config.py + dispatcher.py + page_scrapers.py; bank scripts
└── schemas/automation.py  # Shared types and case normalization
```

| Document                                                | Purpose                                                                 |
| ------------------------------------------------------- | ----------------------------------------------------------------------- |
| [Database guide](database-guide.md)                     | Existing servers, database maintenance, migrations, backup, and restore |
| [Application overview](application-overview.md)         | Terms, navigation, and scope                                            |
| [Collection workflow](collection-workflow.md)           | Source catalog, scraping, automatic suggestions, and function handoff   |
| [Architecture](architecture.md)                         | File responsibilities and where to change code                          |
| [Feature framework](feature-framework.md)               | Saving, completion, and progress                                        |
| [Labeling field reference](labeling-field-reference.md) | Every field, allowed values, examples, and scale definitions            |
| [Comparison](comparison.md)                             | Selection and result interpretation                                     |
| [API reference](api-reference.md)                       | Endpoints and contracts                                                 |
| [Development checks](development.md)                    | Build and manual verification                                           |

Keep documentation in English. Update the relevant guide and link to it instead of copying instructions between files.
