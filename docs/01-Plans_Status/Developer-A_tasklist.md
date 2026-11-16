# Tasklist — Developer A

**Owner:** Ralph

**Scope:** Unstructured sources, OCR, chunking, embedding/indexing and retrieval

**Updated:** 16 Nov 2026 (SGT). Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies clean_cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Review initial audit; complete visual/content checks of every POD/email/rate card and record source coverage and uncertainty | 20 Nov, 17:00 | ⏳ |
| 2 | Verify Q02–Q05 source wording; check original archive with B/E; John sends and records replies | 16–17 Nov | ⏳ |
| 3 | Agree POD/rate record and citation schema with B/C; publish synthetic sample | 17 Nov | ⏳ |
| 4 | Implement source-aware chunking/overlap, source/date/system metadata, embedding/index versions and caching; validate relevant-source retrieval/citations with Jeffrey’s realistic queries; guide processing waits for supplied guide | 17 Nov design; 18–23 Nov implementation | ⏳ |
| 5 | Produce one validated image extraction handoff to B/C for the Friday integrated rehearsal | 20 Nov internal; 23 Nov, 09:00 checkpoint | ⏳ |
| 6 | Implement per-file manifest, caching, bounded retries and visible extraction errors; coordinate paid runs | 23 Nov | ⏳ |
| 7 | Supply cited search_policy/search_emails and extracted records; unavailable guide returns an honest missing-source result | 23–24 Nov | ⏳ |
| 8 | Supply five checkable extraction/chunking/retrieval clean_cases with source expectations, relevance and citation checks; document embedding or lexical choice; fix own failures; instrument tools/extraction using C contract | 24 Nov | ⏳ |
| 9 | Provide source limitations, image evidence and sanitised citations to B/C/D/E for final report and demo | 26 Nov | ⏳ |

## Table creation and repeatable loading

Create and batch-load clean_pod_evidence, clean_policy_rules, clean_rate_cards, clean_rate_prices, clean_rate_surcharges and clean_complaint_emails using existing extraction outputs. Supply migrations, parameterised loaders, source lineage and rerun/new-batch checks; B/C review. Excel guide support and client-confirmed rate rules must be added.

**Planned:** 18–23 Nov. **Status:** ⏳ SQL creation/loading not implemented in the reviewed code; existing extraction is a separate deliverable. See [table owners and batch contract](../02-Design/database-design_2026-11-16.md#11-owner-delivery-contract--creation-and-loading-are-one-deliverable). Each owner must provide executable creation and loading, not just a design or output file.
