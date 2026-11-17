# Tasklist — Developer D

**Owner:** Jeffrey Kong

**Scope:** React customer journey, business acceptance, client-facing presentation and pitch

**Updated:** 17 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Verify shared setup; define realistic complaint/weekly journeys and useful answer/clarification expectations with A/B/C; help phrase client questions | 17 Nov | ⏳ |
| 2 | Review reusable Simple CRM frontend patterns and adapt layout/forms/API/loading/error patterns to current React scaffold. *17 Nov: patterns applied (Lessons 2.5 fetch/`response.ok`, 2.6 Context+reducer, 2.11 `VITE_` config/validation); PR `feature/d-triage-weekly-mock-ui` pending; local `npm run lint`/`build` still to run.* | 17–18 Nov | 🚧 |
| 3 | Implement complaint input, submit/loading/error/retry and ambiguity clarification using C synthetic responses. *17 Nov: implemented against D's own synthetic mock (7 journeys); switch to C's fixtures/API when published. Evidence: handoff `Jeffrey_2026-11-17-frontend-mock-ui.md`, screenshots in `docs/02-Design/ui-screenshots/`. 17 Nov (later): C agreed and froze the HTTP-01–03/06 contract in the [frontend contract](../02-Design/frontend-ui-contract-draft.md) §5 — wire against the real API (see also the [TOOL-05 handoff](../03-Handoffs/John_2026-11-17-tool05-sql-provider.md)); weekly parts stay proposed.* | 18–20 Nov | 🚧 |
| 4 | Connect C HTTP API; show resolved order, evidence/conflicts, recommendation/abstention and accessible citations. *17 Nov: C's API runs a real SQL-backed flow locally (real candidates from MySQL, cited POD/policy evidence, restart recovery); wire against it per the [TOOL-05 handoff](../03-Handoffs/John_2026-11-17-tool05-sql-provider.md) (D section), then the joint thin-flow call.* | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 5 | Build weekly view with period selection, reporting definitions and unknown attribution from B/C result. *17 Nov: UI built on synthetic data (week picker, zone filter, KPIs, 5 charts, definitions); waits for B's `weekly_complaints` and definition sign-off.* | 23–24 Nov; client-dependent | 🚧 |
| 6 | Support follow-ups/session IDs and user-visible recovery after backend restart; no model key in browser | 24 Nov | ⏳ |
| 7 | Contribute three journey/citation cases; run frontend lint/build and own UI fixes; E maintains shared runner. *17 Nov: draft cases D-J01–J03 in `evals/developer_d_cases.json`, expectations to be verified by B/C.* | 24 Nov | 🚧 |
| 8 | Supply sanitised screenshots; own pitch deck/business value narrative and client-facing demo storyline; choose UI operator/backup with E/C at rehearsal | 23 Nov storyline; 24 Nov rehearsal; 26 Nov final; 27 Nov presentation | ⏳ |

## Presentation and business review

Jeffrey leads the five-minute pitch and client-facing demo/Q&A. John validates technical claims, leads technical Q&A and sends/logs official emails; A/B provide source facts; E maintains the runbook and supports rehearsal/recovery. Record the application operator/backup on 24 Nov so presentation and laptop operation can be handled by different people.

Review realistic retrieval queries with Ralph and contribute the three journey cases to Wai Hong's shared suite. Review business usefulness across scenarios; A/B/C verify source facts and policy rules. Do not invent client policy or take ownership of backend implementation. Prioritise working React integration before elaborate deck design.
