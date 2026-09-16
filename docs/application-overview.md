# Application Overview

[Documentation index](README.md)

## Purpose

Compare how bank webpages communicate similar products using manually recorded observations. The workflow is **Dataset → Label → Compare → Insights**. There is no scraper, automatic analysis, or AI scoring.

## Terms

| Term | Meaning | Example |
| --- | --- | --- |
| Campaign | One saved webpage to review | A bank's current-account landing page |
| Bank | The organization publishing the page | ING |
| Product | The specific offer named on the page; recorded during labeling | A named account package |
| Category | The shared product family used to group comparisons | Current Account (`current_account`) |
| Labeling | Structured observations about the page | Language, word count, tone, CTA prominence |
| Evaluation | Optional, separate five-score subjective assessment | Clarity score |

The API calls a category `project`. **Settings → Add product** currently manages these categories, not the product-name field in labeling.

## Navigation and pages

The sidebar contains **Dataset**, **Compare**, and **Settings**. Settings contains **Add campaign**, **Add bank**, and **Add product**.

| Route | Purpose |
| --- | --- |
| `/` | Dataset, counts, filters, and campaign deletion |
| `/campaigns/new` | Create a campaign |
| `/campaigns/:id` | Campaign context and communication details |
| `/campaigns/:id/edit` | Edit bank, category, and source URL |
| `/campaigns/:id/label` | Label features and complete review |
| `/compare` | Select comparable pages and inspect findings, chart, and table |
| `/campaigns/:id/evaluate` | Optional subjective evaluation |
| `/banks/new` | Manage bank options |
| `/projects/new` | Manage category options |

Open a campaign by clicking its bank name in Dataset, then enter labeling. Dataset's Actions column only contains Delete. Campaign options expose secondary editing and evaluation tasks. Insights is a section within comparison, not a separate analysis page.

## Data and review status

Campaign context supplies the bank, category, and source URL. Feature labeling adds product name, language, review date, and analytical observations. Details and optional evaluations remain independent of framework labels.

- **Not Started:** no saved labeling record.
- **In Progress:** a draft has been saved.
- **Completed:** completion was accepted, possibly with acknowledged missing fields.

Dataset's In progress summary counts campaigns whose labeling is not completed, including those not started. Completion does not guarantee 100% field coverage.

## Research and demo data

Real and demo modes use separate PostgreSQL databases. The header identifies the active mode. Demo bank names are normal names, but values are synthetic and source URLs are placeholders. Use them to explore the workflow, not as research evidence.

See [feature definitions and progress](feature-framework.md), [comparison rules](comparison.md), and [database operations](database-guide.md).
