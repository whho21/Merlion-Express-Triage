# Tasklist — Developer B

**Owner:** Jenn Fang

**Scope:** Python/pandas profiling, data cleaning, MySQL, identity and analytics

**Updated:** 16 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies clean_cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Reproduce audit counts in native MySQL; document common raw import and reconcile loaded counts with all five setups | 17–20 Nov | ⏳ |
| 2 | Profile SQL/GPS using pandas; investigate composite identities, delivery gaps, postal semantics and time alignment; update audit/traps | 20 Nov, 17:00 | ⏳ |
| 3 | Verify structured questions Q01/Q03–Q06 with A/E; John sends; preserve unresolved business rules | 16–17 Nov | ⏳ |
| 4 | Agree extraction/lookup/tool schemas with A/C; publish fixture and cleaned Mermaid ER | 17 Nov contracts; 20 Nov, 17:00 ER | ⏳ |
| 5 | Build idempotent cleaned loaders and candidate lookup using system_version/order_id; preserve raw timestamps and postal text | 18–23 Nov | ⏳ |
| 6 | Expose cited delivery/POD/GPS/date-sensitive rate tools; use A sample for Friday image integration; do not infer missing rates/attempts | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 7 | Implement weekly driver/zone aggregates only with approved case/time/dedup/zone definitions; expose unknowns and limitations | 23–24 Nov; client-dependent | ⏳ |
| 8 | Supply six checkable data/analytics clean_cases, source-tool telemetry and independently verified totals; fix own failures | 24 Nov | ⏳ |
| 9 | Compile one-page quality report including unresolved limitations and cleaning decisions from all owners | 26 Nov | ⏳ |

## Table creation and repeatable loading

Create and batch-load B-owned operational, raw case, canonical case/member, GPS and zone tables; own safe SQL snapshot staging and relational/dedup rules. Supply migrations, parameterised loaders and fresh/rerun/overlap/interruption checks; A/C review.

**Planned:** 18–23 Nov. **Status:** ⏳ SQL creation/loading not implemented in the reviewed code; existing extraction is a separate deliverable. See [table owners and batch contract](../02-Design/database-design_2026-11-16.md#11-owner-delivery-contract--creation-and-loading-are-one-deliverable). Each owner must provide executable creation and loading, not just a design or output file.

Use `clean_drivers`, `clean_orders`, `clean_deliveries_latest` and other prefixed targets in the single `merlion_express` database. Preserve instructor `drivers`, `orders`, `deliveries`; also supply `view_weekly_complaints_by_driver` and `view_weekly_complaints_by_zone` definitions and validation queries.
