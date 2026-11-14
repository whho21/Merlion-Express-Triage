# Tasklist — Developer B

**Owner:** To be assigned (A–D mapping pending)
**Scope:** Structured data, MySQL and analytics

## Task Legend

- ⏳ — waiting to start
- 🚧 — in progress
- ✅ — completed
- 🙅 — cancelled

The A–D to named-person mapping is still open in `delivery_RID.md` (item 1). Update the owner line after the team agrees it. Dates are Singapore time. Mark a task complete only after its deliverable and check are available; link the PR or evidence in the task text when done. Client data and keys stay out of Git.

## Tasklist

| S/N | Task / evidence of completion | Planned End | Done |
| --: | --- | :-- | :--: |
| 1 | Audit SQL, tabular and GPS files; record counts, keys, duplicates, nulls, parse failures, join coverage and traps in `docs/05-Reviews/` | 19 Nov, 09:00 | ⏳ |
| 2 | Draft evidence-backed client questions on missing guide/files, source authority and timezone; give John wording for the client log | 16–17 Nov | ⏳ |
| 3 | Import the raw SQL dump and define repeatable loading commands; document counts and rejected records | 19 Nov, 09:00 | ⏳ |
| 4 | Propose cleaned order/event keys, timestamp and postal-code rules; add Mermaid ER diagram to `docs/02-Design/architecture.md` | 19 Nov, 09:00 | ⏳ |
| 5 | Agree POD/rate handoff schema and source provenance with A; test loader using a synthetic sample | 17–20 Nov | ⏳ |
| 6 | Build idempotent SQL, tabular, GPS and extracted-image loaders; reconcile source, loaded, rejected and duplicate counts | 23 Nov | ⏳ |
| 7 | Implement cited delivery, POD, GPS-window and date-sensitive rate tools with honest missing/failure outcomes | 23 Nov | ⏳ |
| 8 | Implement weekly complaint counts by driver/zone, period and unknown attribution; document definitions and verify totals | 23–24 Nov | ⏳ |
| 9 | Contribute at least six data-integrity/analytics eval cases, tests and telemetry; compile one-page `docs/04-Testing_Evals/data_quality_report.md` | 24–26 Nov | ⏳ |
