# Tasklist — Developer A

**Owner:** Ralph

**Scope:** Unstructured sources, OCR, chunking, embedding/indexing and retrieval

**Updated:** 17 Nov 2026 (SGT) — statuses by Ralph with evidence. Source of truth: [team plan v0.5](Capstone_TEAM_PLAN_v0.5.md).

Status: ⏳ planned, 🚧 in progress, ✅ verified complete, 🙅 cancelled. Mark complete only with a PR/evidence link and an executed acceptance check. Initial audit observations do not establish that this owner's implementation is complete. Each owner verifies local data, supplies cases, fixes their own component and writes developer-reviewed dependent-work handoffs. Client data and secrets stay outside Git.

Checkpoint 1 is **Fri 20 Nov, 17:00 SGT**; Checkpoint 2 remains **Mon 23 Nov, 09:00 SGT**.

| S/N | Task / evidence of completion | Planned end | Status |
|---:|---|---|---|
| 1 | Review initial audit; complete visual/content checks of every POD/email/rate card and record source coverage and uncertainty | 20 Nov, 17:00 | ✅ PR #5: every email/POD/rate card opened; `data_audit_2026-11-16.md` A section; image run 80/80 POD key fields match SQL, rate card 12/12 (handoff 16 Nov) |
| 2 | Verify Q02–Q05 source wording; check original archive with B/E; John sends and records replies | 16–17 Nov | ✅ John sent 16 Nov 6:42 PM; client replied Q01–Q08 8:00 PM; guide + case log arrived as a separate attachment; A-Q5 answered by the case log (73/79 senders) — `package_reconciliation_2026-11-16.md` |
| 3 | Agree POD/rate record and citation schema with B/C; publish synthetic sample | 17 Nov | 🚧 synthetic samples for POD/rate/email/policy published in `contracts_2026-11-16.md` §1–§6 (updated 17 Nov); agreement with B/C at the 17 Nov sync |
| 4 | Implement source-aware chunking/overlap, source/date/system metadata, embedding/index versions and caching; validate relevant-source retrieval/citations with Jeffrey’s realistic queries; guide processing waits for supplied guide | 17 Nov design; 18–23 Nov implementation | 🚧 email + guide retrieval with exact locators, guide version/date metadata, cached outputs; keyword choice documented and measured (`Ralph_2026-11-17-guide-and-client-answers.md`). **17 Nov team decision: embeddings + FAISS + SQLite added** (hybrid search with keyword fallback, masked text embedded, cached, stale guard; 84 unit tests) — `Ralph_2026-11-17-vector-index.md`. Real index build blocked: team key out of credit. Then: calibrate threshold, measure modes on Jeffrey's queries |
| 5 | Produce one validated image extraction handoff to B/C for the Friday integrated rehearsal | 20 Nov internal; 23 Nov, 09:00 checkpoint | 🚧 validated `pod_records.jsonl` / `rate_cards.jsonl` ready (PR #5, cited answer in the 16 Nov handoff); file hand-over to B/C by an agreed private route pending |
| 6 | Implement per-file manifest, caching, bounded retries and visible extraction errors; coordinate paid runs | 23 Nov | ✅ PR #5: per-file manifests, cache by image+prompt+model, 3 bounded retries, failed records kept, spend log (`api_spend.md`, US$0.32) |
| 7 | Supply cited search_policy/search_emails and extracted records; unavailable guide returns an honest missing-source result | 23–24 Nov | 🚧 `search_emails` / `search_policy` (with guide, by category) and records built; honest `SOURCE_MISSING` / `not_found` paths tested; C integration pending |
| 8 | Supply five checkable extraction/chunking/retrieval cases with source expectations, relevance and citation checks; document embedding or lexical choice; fix own failures; instrument tools/extraction using C contract | 24 Nov | 🚧 18 cases in `evals/developer_a_cases.json`, 18/18 pass; lexical choice documented; telemetry lines drafted (contracts §6) until C's contract |
| 9 | Provide source limitations, image evidence and sanitised citations to B/C/D/E for final report and demo | 26 Nov | 🚧 draft in `Ralph_2026-11-16-A-tools-evidence-limits.md` + 17 Nov handoff; final pass before 26 Nov |

## Table creation and repeatable loading — current versus future

Current phase: retain file-backed evidence tools and deliver Excel guide ingestion, confirmed rate rules, source/version manifests and repeatable batch processing. No MySQL migration is required now. Future enhancement owner: clean_pod_evidence, clean_policy_rules, clean_rate_cards, clean_rate_prices, clean_rate_surcharges and clean_complaint_emails; provide DDL/loaders only if approved.

**Status:** Current case-table migrations/loaders and views are pending in reviewed code; existing A extraction/search is a separate implemented component. See [phase-labelled database inventory](../02-Design/database-design_2026-11-16.md#3-complete-proposed-data-table-inventory) for all final-state tables, owners and statuses. Current owners must supply teammate-runnable setup/batch code and checks; future SQL deliverables require a promotion decision first.
