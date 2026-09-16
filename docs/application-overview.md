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

## Categories

### Banks

| Bank     | website                           | Nb customers | Category    |
| -------- | -------                           | ------       | -------     |
| BNP      | https://www.bnpparibasfortis.be/  | 3.5 M        | Traditional |
| Belfius  | https://www.belfius.be/           | 3.5 M        | Traditional |
| KBC      | https://www.kbc.be/               | 3.4 M        | Traditional |
| ING      | https://www.ing.be/               | 2.5 M        | Traditional |
| Argenta  | https://www.argenta.be/           | 1.7 M        | Traditional |
| Crelan   | https://www.crelan.be/            | 1.2 M        | Traditional |
| Revolut  | https://www.revolut.com           | 1 M          | Neobank     |
| Beobank  | https://www.beobank.be            | 0.75 M       | Traditional |

### Products

| Category                         | Product                               | Description                                                      | French                        | Dutch                       |
| -------------------------------- | ------------------------------------- | ---------------------------------------------------------------- | ----------------------------- | --------------------------- |
| **Day-to-day banking**           | Current Account                       | For day-to-day payments                                          | Compte courant / Compte à vue | Zichtrekening               |
| **Day-to-day banking**           | Youth Account                         | Aimed at children, teenagers, and young adults                   | Compte Jeunes                 | Jongerenrekening            |
| **Day-to-day banking**           | Credit Card                           | For delayed payments                                             | Carte de crédit               | Kredietkaart                |
| **Savings**                      | Savings Account                       | To park money while earning a modest interest return             | Compte d'épargne              | Spaarrekening               |
| **Savings**                      | Term Account                          | Fixed-term investment tool                                       | Compte à terme                | Termijnrekening             |
| **Savings**                      | Pension Saving Plan                   | Locked until pension                                             | Épargne-pension               | Pensioensparen              |
| **Loans**                        | Vehicle Loan                          | For buying a vehicle                                             | Crédit auto                   | Autolening                  |
| **Loans**                        | Renovation & Eco-Energy Loan          | For renovating real estate                                       | Crédit rénovation / énergie   | Renovatie- en energielening |
| **Loans**                        | Multi-Purpose Loan                    | For financing hobbies, events, furniture, or unexpected expenses | Crédit confort                | Persoonlijke lening         |
| **Loans**                        | Mortgage Loan                         | For purchasing, building, or renovating real estate              | Crédit hypothécaire           | Woonkrediet                 |
| **Loans**                        | Bridge Loan                           | When buying a new house while waiting to sell the current one    | Crédit pont                   | Overbruggingskrediet        |
| **Insurance**                    | Car Insurance                         | Protection against car accidents                                 | Assurance auto                | Autoverzekering             |
| **Insurance**                    | Home Insurance                        | Protection for the house                                         | Assurance habitation          | Brandverzekering            |
| **Insurance**                    | Family Insurance                      | Against everyday accidents caused by children, pets, bikes, etc. | Assurance familiale           | Familiale verzekering       |
| **Insurance**                    | Travel Insurance                      | Emergency repatriation and cancellation protection               | Assurance voyage              | Reisverzekering             |
| **Insurance**                    | Outstanding Balance Insurance         | Death insurance tied directly to the mortgage                    | Assurance solde restant dû    | Schuldsaldoverzekering      |
| **Investment & Wealth Products** | Investment Fund / Regular Saving Plan | —                                                                | Plan d'investissement         | Beleggingsplan              |
| **Investment & Wealth Products** | Online Trading & Securities Account   | —                                                                | Compte-titres                 | Effectenrekening            |


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
