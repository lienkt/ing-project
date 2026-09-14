# Banking campaigns comparator — Frontend

React, TypeScript, Vite, React Router, and a shared fetch client. A responsive internal research workspace with sidebar navigation, campaign table, filters, controlled forms, status badges, and manual scoring.

## Start

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Open http://localhost:5173. Start the backend separately as described in the root README. `VITE_API_URL` defaults to `http://localhost:8000`; restart Vite after changing `.env`.

```bash
npm run build
npm run preview
```

The build runs strict TypeScript checks and creates `dist/`. Preview typically uses port 4173; add `http://localhost:4173` to backend `CORS_ORIGINS` when using it. A production static server must route unknown application paths to `index.html` for React Router.

## Pages and routing

| Route | Page |
| --- | --- |
| `/` | Campaign overview, counts, bank/project filters, text search, record actions |
| `/campaigns/new` | Bank, project, source URL creation form |
| `/campaigns/:id/edit` | Edit saved bank, project, and source URL |
| `/campaigns/:id` | Source context and editable communication details |
| `/campaigns/:id/evaluate` | Five required manual scores, notes, save confirmation |

`src/main.tsx` defines the shared layout and routes. `src/pages/` holds page components. `src/components/shared.tsx` contains status badges, notices, loading state, campaign context, workflow steps, and a record-loading hook. `src/styles.css` provides the responsive design. Optional Google Fonts fall back to local sans-serif fonts when offline.

## API integration

`src/api/campaigns.ts` contains shared types, project options, label formatting, error handling, and these functions:

- `getCampaigns(filters?)`
- `getCampaign(id)`
- `createCampaign(data)`
- `updateCampaignDetails(id, data)`
- `evaluateCampaign(id, data)`

Pages use these functions instead of issuing raw requests. The dashboard filters the loaded library locally; the backend also supports bank/project filters. No sample records or browser-only persistence are used. All saves go to the backend database.

Native form constraints and backend validation surface errors. Buttons are disabled during saves, and details must be saved before using the Continue to Evaluation button. Evaluations preload saved scores and never calculate overall score. Loading failures include clear messages; the dashboard offers retry. Unknown routes show a return link.

## Manual UI check

Run both services, create a campaign, return to the dashboard, filter it, edit details, save, continue to evaluation, choose all five scores, and save. Return to the dashboard and confirm Evaluated status. Reopen and refresh the campaign to verify persistence. Test a narrow screen and keyboard navigation through score radios and forms.

For saved campaigns, all three workflow steps are links. Revisit Basic information, Campaign details, or Evaluation at any time, including after evaluation. Save each form before switching steps. Editing campaign information preserves existing observations and scores; review scores manually when changes affect the evaluation.

The sidebar also includes **Add bank** (`/banks/new`) and **Add project** (`/projects/new`). Each page saves named options through the API and lists existing options. Saved banks appear as campaign bank suggestions; saved projects appear in the project dropdown on both create and edit forms.

## Management controls

Click a campaign name on the dashboard to open it, then use the workflow steps to edit basic information, details, or evaluation. The dashboard only shows the Delete icon in its actions column. Delete asks for confirmation and removes its details and evaluation too. The Add bank and Add project sidebar entries open management pages with add forms and Edit/Delete controls for every saved option. Edit preloads the form; Cancel edit restores add mode. Renaming updates linked campaigns; deleting an option used by campaigns shows an error explaining that those campaigns must first be reassigned or deleted.
