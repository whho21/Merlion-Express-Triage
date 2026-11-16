# Tasklist — Developer C

**Owner:** John Phang

**Scope:** Python API, agent services, state/guardrails and Captain coordination

**Updated:** 16 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies clean_cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Review technical accuracy of client questions framed with Jeffrey after archive check; send official emails; log actual date/replies and project impact; track deadline risks | 16–17 Nov, then daily | ⏳ |
| 2 | Confirm endpoint capabilities/rates/budget and minimum Python stack with measured smoke sample | 16–17 Nov | ⏳ |
| 3 | Publish API/tool/citation/session/error/telemetry contracts and synthetic examples; give E a working runner starter and case schema | 17 Nov | ⏳ |
| 4 | Implement thin validated HTTP routes and agent service; connect D React and B candidate lookup | 18–20 Nov | ⏳ |
| 5 | Compile proposed architecture and Mermaid flow with A/B/D; record recommendation-only boundary | 20 Nov, 17:00 | ⏳ |
| 6 | Deliver query-time SQL plus image flow with grounded citations; clarify ambiguity and abstain when policy is missing | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 7 | Implement persistent sessions/restart, deterministic input refusals, output checks, evidence validation and bounded dependency failure handling | 24 Nov | ⏳ |
| 8 | Own model telemetry/daily spend, review E runner/configuration and contribute eight clean_cases including five kill-shot phrasings and at least two refusals | 24 Nov | ⏳ |
| 9 | Document backend recovery, coordinate five attributable contributions, checkpoint merges and submission; validate Jeffrey’s pitch claims and lead technical Q&A | 20–27 Nov | ⏳ |

## Table creation and repeatable loading

Create/load meta_source_documents and meta_ingestion_runs; provide shared configuration/provenance APIs and setup/batch orchestration with publish/rollback semantics. Review owner migrations and preserve existing source evidence.

**Planned:** 17–23 Nov. **Status:** ⏳ SQL creation/loading not implemented in the reviewed code; existing extraction is a separate deliverable. See [table owners and batch contract](../02-Design/database-design_2026-11-16.md#11-owner-delivery-contract--creation-and-loading-are-one-deliverable). Each owner must provide executable creation and loading, not just a design or output file.
