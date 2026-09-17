# Feature Framework

[Documentation index](README.md) · [All fields and scale definitions](labeling-field-reference.md)

## Label a page

Open a campaign from Dataset, enter labeling, and inspect **Open Original Page**. Work through the eight sections; use notes for uncertainty or counting exceptions.

## Save and complete

| Action | Result |
| --- | --- |
| Change a value | Autosaves after 1.2 seconds of inactivity |
| Save Draft | Saves immediately; status becomes In Progress |
| Complete Labeling | Sets Completed; requires at least one filled field and confirmation of any omissions |
| Save edits to completed labels | Returns status to In Progress |

Review metadata counts toward the completion minimum. An empty record cannot be completed. Failed saves retain entered values for retry; browser local storage also holds unsaved edits for recovery.

## Progress

Progress is the rounded percentage of **68 framework fields** that are filled, including review metadata and the derived average. Zero and false count; null and empty text do not. Notes and system fields are excluded.

There are no automatic applicability rules. Explain inapplicable fields in notes and leave them unset; Completed can therefore be below 100%.

## Persistence

Each campaign has one current feature record, separate from communication details and optional evaluation. Saves have no stale-edit conflict detection; coordinate editing within the team.

Labeling supports manual entry and [automatic suggestion review](collection-workflow.md). The current extraction engine is a demo only. Provenance is record-level, not a per-field history; explicitly saving a reviewed proposal uses `manual_override`. During proposal review, autosave is disabled until an explicit review save.

See [field reference](labeling-field-reference.md) for values and [API reference](api-reference.md#feature-labeling) for request contracts.
