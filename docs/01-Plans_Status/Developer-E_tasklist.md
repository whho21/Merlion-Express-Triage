# Tasklist — Developer E

**Owner:** Ho Wai Hong

**Scope:** Setup verification, evaluation runner, integration checks and demo runbook

**Updated:** 16 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Check original archive/separate attachments with A/B; reconcile package checklist; do not describe draft questions as sent | 16–17 Nov | ⏳ |
| 2 | Follow seeding guide and collect all five developers local count confirmations without credentials/client records | 17–20 Nov | ⏳ |
| 3 | Use C starter/API fixture/case schema to implement first local five-case runner; C reviews first working increment. *18 Nov (early): C contributed 26 HTTP-01–03 cases in a step/expect schema (`evals/complaint_api_http_cases.json`; 19 synthetic, 7 sql-gated, 4 refusals, 5 kill-shots) — see [eval cases handoff](../03-Handoffs/John_2026-11-17-eval-cases-http01-03.md).* | 18–19 Nov | ⏳ |
| 4 | Verify synthetic React → API flow and maintain smoke checklist; record actual commands/results and component owners | 20 Nov, 17:00 | ⏳ |
| 5 | Run Friday SQL/image cited-flow rehearsal with A/B/C/D and Checkpoint 2 verification; report blockers | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 6 | Extend runner with owner-supplied cases and explicit content/source assertions; contribute four integration/restart/failure cases; use Jeffrey’s business scenarios with component-owner-verified expectations | 24 Nov | ⏳ |
| 7 | Consolidate at least 20 passing cases, at least two refusals and five kill-shot phrasings; keep client data local and sanitise results | 24 Nov | ⏳ |
| 8 | Add CI lint/build/synthetic checks only after local runner works and C reviews; record manual alternative if permissions block CI | 24–26 Nov; optional | ⏳ |
| 9 | Own demo runbook, full-stack startup/health/restart checks and evidence collection with D/C; record presenter Jeffrey plus operator/backup at 24 Nov rehearsal; rehearse before reporting ready | 26 Nov | ⏳ |

## Table creation and repeatable loading — current versus future

Current phase: maintain sourced/versioned calendar lookup files and verify owner setup, rerun, new/overlapping-batch and recovery procedures through the consolidated suite. clean_calendar_dates is a future enhancement; a calendar SQL migration is not currently required.

**Status:** Current case-table migrations/loaders and views are pending in reviewed code; existing A extraction/search is a separate implemented component. See [phase-labelled database inventory](../02-Design/database-design_2026-11-16.md#3-complete-proposed-data-table-inventory) for all final-state tables, owners and statuses. Current owners must supply teammate-runnable setup/batch code and checks; future SQL deliverables require a promotion decision first.
