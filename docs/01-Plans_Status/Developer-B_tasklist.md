# Tasklist — Developer B

**Owner:** Jenn Fang

**Scope:** Python/pandas profiling, data cleaning, MySQL, identity and analytics

**Updated:** 16 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Reproduce audit counts in native MySQL; document common raw import and reconcile loaded counts with all five setups | 17–20 Nov | ⏳ |
| 2 | Profile SQL/GPS using pandas; investigate composite identities, delivery gaps, postal semantics and time alignment; update audit/traps | 20 Nov, 17:00 | ⏳ |
| 3 | Verify structured questions Q01/Q03–Q06 with A/E; John sends; preserve unresolved business rules | 16–17 Nov | ⏳ |
| 4 | Agree extraction/lookup/tool schemas with A/C; publish fixture and cleaned Mermaid ER | 17 Nov contracts; 20 Nov, 17:00 ER | ⏳ |
| 5 | Build idempotent cleaned loaders and candidate lookup using system_version/order_id; preserve raw timestamps and postal text. *17 Nov: candidate-lookup ownership moved to C (RID item 20, merged as PR #17); B's remaining scope is loaders, weekly views and definitions.* | 18–23 Nov | ⏳ |
| 6 | Expose cited delivery/POD/GPS/date-sensitive rate tools; use A sample for Friday image integration; do not infer missing rates/attempts | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 7 | Implement weekly driver/zone aggregates only with approved case/time/dedup/zone definitions; expose unknowns and limitations. *17 Nov (night): C implemented the HTTP-04/05 exposure boundary with proposed definitions (Mon–Sun SGT by Date Opened, dedup via case groups, compliments excluded, zone from address town, guide gaps per Q02) in `backend/api_service/weekly.py` — confirm or amend these before your loaders land.* | 23–24 Nov; client-dependent | ⏳ |
| 8 | Supply six checkable data/analytics cases, source-tool telemetry and independently verified totals; fix own failures | 24 Nov | ⏳ |
| 9 | Compile one-page quality report including unresolved limitations and cleaning decisions from all owners | 26 Nov | ⏳ |

## Table creation and repeatable loading — current versus future

Current phase: create/load raw_case_log, clean_cases and clean_case_members; supply view_weekly_complaints_by_driver and view_weekly_complaints_by_zone. Join preserved instructor tables using validated system/order identity. Keep reviewed GPS/zone tools file-backed where appropriate. Cleaned operational/GPS/zone tables are future enhancements, not current dependencies.

**Status:** Current case-table migrations/loaders and views are pending in reviewed code; existing A extraction/search is a separate implemented component. See [phase-labelled database inventory](../02-Design/database-design_2026-11-16.md#3-complete-proposed-data-table-inventory) for all final-state tables, owners and statuses. Current owners must supply teammate-runnable setup/batch code and checks; future SQL deliverables require a promotion decision first.
