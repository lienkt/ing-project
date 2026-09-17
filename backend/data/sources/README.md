# Example Source Catalog

The three bank files contain **example.com placeholders**, not verified bank pages or evidence. They demonstrate selection and import only. No large real source list is bundled.

Each file contains `{"sources": [...]}`. Each entry must satisfy `SourceDefinition` in `app/scraping/contracts.py`. Use a stable `source_id`, an existing product-category key (such as `current_account`), and full language names matching the framework.

Keep IDs stable after import. `is_example=true` prevents a real scraper from treating these fixtures as live sources. Replace them with verified URLs and metadata before real collection.

Catalog JSON is not Dataset data. Entries become campaigns only after successful import. Editing files does not update existing campaigns: repeat imports skip them to protect labels.
