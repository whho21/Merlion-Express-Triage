# Frontend — Merlion Express CS Triage Assistant (Developer D)

React 19 + Vite. Owner: Jeffrey Kong (D). Reviewer for API changes: John (C).

The UI runs today against a **synthetic in-browser mock API**, so the customer journey, weekly view and pitch demo can be built and rehearsed before C's backend is ready. Switching to the real API is a config change (see *Configuration*).

## Run it

```bash
cd frontend
npm install
cp .env.example .env.development.local   # optional; defaults to mock mode
npm run dev                               # http://localhost:5173
npm run lint
npm run build
```

No new npm dependencies were added. Charts are small SVG/HTML React components in `src/components/charts/`, so `package-lock.json` is unchanged.

## What is in the UI

| Page | URL | Journeys covered |
|---|---|---|
| Complaint triage | `#/triage` | Normal cited answer · ambiguous v1/v2 order → clarification → follow-up · source conflict shown side by side · approval-required recommendation · "not on file" · guardrail refusal · backend error → Retry · resume session after restart |
| Weekly insights | `#/weekly` | Week picker (Mon–Sun SGT) · zone filter · KPI tiles · stacked weekly columns by zone (click to open a week) · top drivers · complaints by zone · zone × category heatmap · resolution mix donut · counting definitions · limitations · sources |
| How it works | `#/how-it-works` | Client-facing explainer for the pitch: 5-step pipeline, guardrails, known data limits from client answers Q01–Q08 |

In mock mode a **Demo scenario** picker on the triage page loads one synthetic email per journey.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `VITE_API_BASE_URL` | empty | C's API base URL, e.g. `http://localhost:8000` |
| `VITE_USE_MOCK` | `true` | `false` calls the real API (requires `VITE_API_BASE_URL`) |

**Never put the LLM key in a `VITE_` variable.** Vite copies `VITE_` values into browser JavaScript (Lesson 2.11). The key stays in the backend's `.env`.

## Code map (class patterns reused from Module 2)

```
src/
  api/client.js          single place that calls the backend; checks response.ok, timeout (Lesson 2.5)
  api/mockServer.js      synthetic mock of C's API; sessions kept in sessionStorage for restart demo
  api/errors.js          ApiError {status, code, retryable}
  config.js              import.meta.env + VITE_ prefix (Lesson 2.11)
  contexts/              TriageProvider + useTriage() — Context + useReducer store (Lesson 2.6)
  reducers/              triageReducer: explicit actions for submit / follow-up / retry / recover
  fixtures/              SYNTHETIC complaint + weekly data (no client data)
  components/triage/     form (validation on submit/blur, Lesson 2.11), status, evidence, conflicts, recommendation, citations
  components/charts/     ChartFrame (legend + "View as table"), StackedColumns, BarList, Heatmap, Donut, GpsTimeline, Sparkline
  layouts/AppShell.jsx   sidebar + mock/live badge
  pages/                 TriagePage, WeeklyPage, HowItWorksPage
  App.jsx                hash routing (#/triage, #/weekly); swap for react-router v7 (Lesson 2.8) if the team adds it
```

## Design rules

- **Every fact has a source.** Numbered citation markers link to a source list (table / file / image + locator).
- **Uncertainty is visible.** Ambiguous orders ask; conflicts are shown side by side; missing sources say "not on file"; unknown zone/driver is hatched grey, never dropped.
- **Recommendation-only.** The UI never shows a "Refund" or "Send" button; approval needs are labelled.
- **Status = icon + words**, never colour alone. Chart colours use a colour-blind-validated categorical palette in fixed entity order; each chart has a "View as table" option.
- **PII**: the UI displays only what the API returns; masking is done server-side (B/C). The mock shows masked values.

## Known gaps / next steps

1. Route paths and JSON fields are D's proposal — see `docs/02-Design/frontend-ui-contract-draft.md`. C confirms or changes them; only `src/api/client.js` should need edits.
2. Swap hash routing for `react-router` (Lesson 2.8) and plain validation for Yup (Lesson 2.11) if the team agrees to add those dependencies.
3. Add Vitest + React Testing Library checks for the triage reducer and journey states (Lesson 2.9).
4. Replace synthetic weekly data with B's `weekly_complaints` via C's API once definitions are signed off.
