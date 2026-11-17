# Tasklist — Developer C

**Owner:** John Phang

**Scope:** Python API, agent services, state/guardrails and Captain coordination

**Updated:** 17 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Review technical accuracy of client questions framed with Jeffrey after archive check; send official emails; log actual date/replies and project impact; track deadline risks | 16–17 Nov, then daily | ⏳ |
| 2 | Confirm endpoint capabilities/rates/budget and minimum Python stack with measured smoke sample | 16–17 Nov | ⏳ |
| 3 | Publish API/tool/citation/session/error/telemetry contracts and synthetic examples; give E a working runner starter and case schema. *17 Nov: starter and contracts implemented; D accepted and froze the HTTP-01–03/06 frontend contract ([contract draft §5](../02-Design/frontend-ui-contract-draft.md)); merged as [PR #17](https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express/pull/17). Pending: E's runner review and durable telemetry/spend.* | 17 Nov | 🚧 |
| 4 | Implement thin validated HTTP routes and agent service; connect D React and B candidate lookup. *17 Nov: complaint/session routes and cached POD/policy adapters implemented ([implementation handoff](../03-Handoffs/John_2026-11-17-complaint-session-api.md)). 17 Nov (later): TOOL-05 live MySQL provider implemented, verified live and merged as [PR #17](https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express/pull/17) ([TOOL-05 handoff](../03-Handoffs/John_2026-11-17-tool05-sql-provider.md)). 17 Nov (night): HTTP-04/05 weekly endpoints implemented behind an injectable weekly source (default unavailable; evals fixture for demo) with C's proposed definitions pending B's confirmation; D integration and assessment/answer orchestration pending.* | 18–20 Nov | 🚧 |
| 5 | Compile proposed architecture and Mermaid flow with A/B/D; record recommendation-only boundary | 20 Nov, 17:00 | ⏳ |
| 6 | Deliver query-time SQL plus image flow with grounded citations; clarify ambiguity and abstain when policy is missing | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 7 | Implement persistent sessions/restart, deterministic input refusals, output checks, evidence validation and bounded dependency failure handling. *17 Nov: SQLite recovery, candidate/source checks, safe refusals, citation validation and bounded calls implemented and checked locally, including a real server restart; live-data/model acceptance and PR review pending. See implementation handoff.* | 24 Nov | 🚧 |
| 8 | Own model telemetry/daily spend, review E runner/configuration and contribute eight cases including five kill-shot phrasings and at least two refusals | 24 Nov | ⏳ |
| 9 | Document backend recovery, coordinate five attributable contributions, checkpoint merges and submission; validate Jeffrey’s pitch claims and lead technical Q&A | 20–27 Nov | ⏳ |

## Table creation and repeatable loading — current versus future

Current phase: configuration, API/agent/policy checks, persistent sessions and manifest-based orchestration linking consistent SQL and file versions. meta_source_documents and meta_ingestion_runs are future enhancements; do not make current loading depend on those tables.

**Status:** Current case-table migrations/loaders and views are pending in reviewed code; existing A extraction/search is a separate implemented component. See [phase-labelled database inventory](../02-Design/database-design_2026-11-16.md#3-complete-proposed-data-table-inventory) for all final-state tables, owners and statuses. Current owners must supply teammate-runnable setup/batch code and checks; future SQL deliverables require a promotion decision first.
