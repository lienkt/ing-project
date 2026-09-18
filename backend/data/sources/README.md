# Example Source Catalog

The three bank files contain **example.com placeholders**, not verified bank pages or evidence. They demonstrate selection and import only. No large real source list is bundled.

Each file contains `{"sources": [...]}`. Each entry must satisfy `SourceDefinition` in `app/schemas/automation.py`. Use a stable `source_id`, an existing product-category key (such as `current_account`), and a supported language name or EN/NL/FR code.

Keep IDs stable after import. `is_example=true` prevents a real scraper from treating these fixtures as live sources. Replace them with verified URLs and metadata before real collection. Adding a catalog entry does not enable automation: register a finished function in the appropriate support config.

Catalog JSON is not Dataset data. Entries become campaigns only after successful import. Editing files does not update existing campaigns: repeat imports skip them to protect labels.
