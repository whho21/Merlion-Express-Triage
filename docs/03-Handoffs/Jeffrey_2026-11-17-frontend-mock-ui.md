# Handoff

**From**: Jeffrey Kong (Developer D)
**To**: John Phang (C — API contract review); Jenn Fang (B — weekly definitions); Ho Wai Hong (E — journey/smoke checks)
**Date-Timestamp**: 2026-11-17 (SGT)
**Topic**: D tasks 2–3 — React triage journey and weekly insights UI on synthetic mock data
**Branch / PR**: `feature/d-triage-weekly-mock-ui` → instructor `main` (PR pending review; not merged)

## Scope

- Replaced the Vite starter page in `frontend/` with the CS Triage Assistant UI. **No new npm dependencies**; charts are small SVG/HTML components.
- **Complaint triage** (`#/triage`): email form with validation; loading state; error + Retry; status banner; order card; evidence cards (delivery, POD, GPS distance chart, rate card); side-by-side source conflicts; recommendation card with approval flag; "not on file" and guardrail-refusal states; numbered citations linked to a source list; follow-up questions in the same session; resume last session after restart.
- **Weekly insights** (`#/weekly`): week picker (Mon–Sun SGT), zone filter, unknown-attribution toggle, five KPI tiles, stacked weekly columns by zone, top drivers, complaints by zone, zone × category heatmap, resolution-mix donut, counting definitions, limitations and sources. Every chart has "View as table".
- **How it works** (`#/how-it-works`): client-facing explainer for the pitch (pipeline, guardrails, data limits from client answers Q01–Q08).
- Mock API (`frontend/src/api/mockServer.js`) built only from synthetic fixtures. Seven journeys: late/cited, ambiguous v1/v2 → clarification, COD conflict, approval > $50, not on file, refusal, failure → retry.
- Proposed consumer contract: `docs/02-Design/frontend-ui-contract-draft.md`.
- Draft journey eval cases: `evals/developer_d_cases.json` (3 cases).

## Checks actually run (17 Nov)

| Check | Result |
|---|---|
| Bundle all of `frontend/src` with esbuild (JSX, CSS modules) | Pass, no errors or warnings |
| Headless Chromium walk-through of all 7 triage journeys, follow-up, reload + resume session, weekly week change / zone filter / table view, How-it-works | Pass, 0 console errors; 17 screenshots |
| Unused variables/imports (TypeScript `--noUnusedLocals` over the JS) | 0 findings |
| Categorical chart palette validated for colour-blind separation (5 slots, light mode) | Pass; low-contrast slots mitigated by direct labels + table view |
| `npm run lint` / `npm run build` with the project's own ESLint + Vite | **Not run in the authoring environment (npm registry unreachable). Run locally before merge.** |

## Remaining

- Route paths/JSON fields are a proposal until C confirms (contract draft §4 questions).
- Weekly numbers are synthetic; needs B's `weekly_complaints` and agreed definitions (dedup rule, compliments, zone from address, guide-gap checks).
- react-router (Lesson 2.8), Yup (Lesson 2.11) and Vitest tests (Lesson 2.9) not added — would need new dependencies; team decision.
- Real backend error codes and session recovery behaviour to be checked against C's implementation.
- Masking happens server-side; the UI shows what it receives. Free-text names are not masked by rule (see Ralph's handoff).

## Next Step

- **John (C):** review the contract draft and answer §4; when the first API route runs, set `VITE_USE_MOCK=false` + `VITE_API_BASE_URL` and do one React → API call together (plan gate: 18 Nov thin flow).
- **Jenn (B):** confirm weekly definitions and which guide-gap checks are feasible.
- **Wai Hong (E):** use `evals/developer_d_cases.json` as the D journey cases in the shared runner once C's API exists.
- **Jeffrey (D):** run `npm run lint` and `npm run build` locally; fix anything found; then wire task 4 (real API) and draft the pitch storyline by 23 Nov.
