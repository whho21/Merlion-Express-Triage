# Team 2 Plan — Merlion Express Capstone

- **Version:** 0.5 _(released dataset and five-developer delivery plan.)_
- **Updated:** 16 Nov 2026, SGT. 
- **Status:** Revised working plan; implementation choices and client-dependent rules remain subject to confirmation.
- **Team:** John Phang (Captain), Ralph, Jenn Fang, Jeffrey Kong, Wai Hong.

## 1. Outcome, sources and current baseline

Deliver a complaint-triage assistant that identifies an order, gathers delivery/POD/GPS/rate/policy evidence, exposes conflicts and missing information, and recommends a resolution only where applicable policy supports it. Provide a weekly complaints view by driver and zone with explicit reporting definitions and unknown attribution.

The course submission repository is `https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express`; push branches and merge reviewed PRs into its `main`. Local remote name: `instructor`. The backup repository is not the submission target. Follow [TEAM_WORK_GUIDE.md](TEAM_WORK_GUIDE.md).

| Source | Role |
|---|---|
| `../00-Biz_Requirements/CLIENT_BRIEF.md` | Client outcomes and constraints; root instructor baseline remains unchanged |
| `../05-Reviews/HARNESS_CHECKLIST.md` | Eight grading areas and required evidence |
| `../05-Reviews/CHECKPOINTS.md` | Team checkpoint tracking; Checkpoint 1 revised below |
| `../05-Reviews/data_audit.md`, `package_checklist.md`, `trap_list.md` | Observed release counts, coverage, limits and source risks |
| `../00-Biz_Requirements/client_qa.md` | Draft/sent questions, actual replies and resulting rules |
| `../02-Design/contracts.md` | Minimum tool, API, session, telemetry and evaluation contracts |

Local inspection baseline: `c0b32e5` plus current documentation changes on 16 Nov. React/Vite scaffold and MySQL Compose configuration exist; SQL seeding instructions are in `database/createdb_seed_sql_data.md`. `database/` contains setup documentation; `backend/` and `evals/` were placeholders at that baseline. Do not describe proposed services or checks as implemented.

### Released package and constraints

Package root: `data/team2_merlion_express_package/`. Initial checks found 40 drivers, 25,833 orders, 24,802 deliveries, 60,000 GPS records, 90 emails, 80 POD images and one April 2026 rate card. `tabular/` is empty; the CS case log and Resolution Guide are absent locally. Check the original archive/separate attachments, then send the questions already drafted in the Q&A log. The [audit](../05-Reviews/data_audit.md) distinguishes completed integrity checks from unfinished semantic/OCR/timezone work.

- Use only the class-provided LLM endpoint during assessment; confirm capabilities, pricing and permitted OCR/embedding options through a small measured sample. Never commit keys.
- Process SQL, tabular, images, documents and GPS; missing tabular inputs remain an explicit blocker, not an exemption or invented replacement.
- Facts are retrieved through tools at question time; joins and arithmetic live in code/SQL. Cite original tables/files/images and explain uncertainty or source conflict.
- Keep client data and derived OCR, indexes, traces and session state under ignored local paths. Commit only sanitised aggregates and synthetic fixtures.
- Retain instructor baseline Markdown in the project root unchanged. Record the revised checkpoint date and source clarifications in team documents.
- MVP proposes recommendations only: no refunds, messages or operational writes. C documents the boundary; if execution is added, approval, durable resume and duplicate-execution protection must precede it.

## 2. Named ownership and workload boundaries

| Developer | Name | Primary deliverable | Main handoff / review |
|---|---|---|---|
| A | Ralph | Unstructured EDA, email/document parsers, POD/rate extraction, chunking, embeddings/indexing and cited retrieval | B reviews extracted records; C reviews retrieval/citation interface |
| B | Jenn Fang | Python/pandas profiling and cleaning, cleaned MySQL schema/loaders, identity lookup, SQL/GPS tools and weekly calculations | C reviews identity/query contracts; A verifies image-derived inputs |
| C | John Phang | Python API/framework, HTTP models/routes, agent orchestration, sessions, guardrails and final-answer validation; Captain coordination | D reviews API usability; A/B review evidence rules; E verifies integrated behaviour |
| D | Jeffrey Kong | React customer journey, business scenario acceptance, client-facing narrative, pitch deck and presentation lead | C supplies stable API and synthetic fixtures; E checks full journey |
| E | Ho Wai Hong | Setup/package reconciliation, bounded eval-runner implementation, integration verification and demo runbook | C supplies starter runner/schema and reviews code; A/B/D verify their cases |

D may adapt the team's earlier Simple CRM frontend patterns for layout, forms, API calls and loading/error states after checking dependencies and reuse permission; do not copy its unrelated business rules or credentials. D does not own backend routes or the shared runner.

E starts with count/setup checks and a small runner that loads synthetic cases, calls C's documented API, checks explicit expectations and produces pass/fail summaries. Add one bounded increment at a time. C provides the first working API example, case schema and runner starter by 17 Nov; E owns subsequent implementation and evidence. CI is optional after the local command works and only if repository permissions allow it. E does not own source cleaning, agent decisions or every component's fixes.

C retains the API and framework decisions to avoid splitting critical backend responsibilities. Keep routes thin and the MVP narrow. A/B implement their own tools, retries, provenance and telemetry; E compiles run evidence and spend summaries from those events. Jeffrey leads the business narrative, presentation and client-facing explanation, and helps frame client questions. John validates technical wording, sends/logs official client emails, coordinates delivery/submission and leads technical Q&A. A/B supply source facts; E supports rehearsal and recovery. Do not assume business experience supplies logistics policy: rules still require client/source authority. Review progress daily and reassign a bounded task when needed.

Table-level delivery refinement: the [database design](../02-Design/database-design_2026-11-16.md#3-complete-proposed-data-table-inventory) retains every final-state table with a phase/owner/status. Current SQL scope is B's `raw_case_log`, `clean_cases`, `clean_case_members` and two weekly reporting views, alongside preserved instructor tables. Ralph retains file-backed evidence tools; C uses versioned manifests for orchestration; E maintains calendar lookup files and verifies integration. The other fourteen application tables are future enhancements, not checkpoint dependencies. Current SQL owners supply creation/loading and all file-tool owners supply repeatable batch processing.

Database naming: one `merlion_express` database. Keep instructor `orders`, `drivers`, `deliveries` unchanged; prefix every new table `raw_`, `clean_` or `meta_` and reporting views `view_`. See the database inventory for owner/status and exact names; upstream extraction filenames/tool contracts are unchanged.

### Shared local setup and working rules

1. All five download the approved package, follow [SQL seeding instructions](../../database/createdb_seed_sql_data.md), and verify the same raw table counts. Docker is the main path; an existing local MySQL is supported. E records confirmations without client records or credentials.
2. A/B maintain the common ingestion/extraction procedure; everyone runs it. Reuse approved local caches to avoid five duplicate paid extraction runs; agree secure distribution and endpoint rules before sharing derived client data.
3. One named owner coordinates full paid extraction, caches by source/configuration and records cost. Do not share the class key through Git, chat logs or screenshots.
4. Work on short-lived named branches; peer review and merge daily. Each member makes substantive commits under their own account; pairing uses co-author attribution.
5. Publish synthetic success, ambiguous, missing and failed examples early. Waiting for client answers does not block API/UI scaffolding or testing honest missing-source behaviour.
6. Dependencies get a developer-reviewed handoff in `docs/03-Handoffs/`. The receiver verifies setup and the next action.

## 3. Stage 1 — audit, setup and contracts, 16–20 Nov

| Role | Work and evidence by Checkpoint 1 |
|---|---|
| A / Ralph | Complete visual/content audit of all assigned images/emails, validate rate-card extraction sample, record uncertainty and coverage, draft source questions and processing-manifest design |
| B / Jenn Fang | Reproduce dump counts in native MySQL, profile sources with Python/pandas, investigate keys/status/postal/time issues, propose cleaned ER and repeatable loading/identity rules |
| C / John | Provide API/service/tool/citation/session contracts, synthetic fixtures, backend shell, endpoint capability sample and architecture proposal; review E's runner starter |
| D / Jeffrey | Map customer journey and realistic business acceptance scenarios; help phrase client questions; implement React views against fixtures and document reusable frontend patterns |
| E / Ho Wai Hong | Reconcile original archive against local package with A/B; collect five local setup confirmations; implement first five-case runner and repeatable smoke checklist from C's examples |
| Captain / John | Review/send client questions, record actual dates/replies, track blockers and confirm all five contributors' evidence is merged |

### Checkpoint 1 — Fri 20 Nov 2026, 17:00 SGT

This date supersedes the old Thu 19 Nov date for team planning, per the 16 Nov team update. Do not modify instructor baseline files to erase the historical date. Consult times and Checkpoint 2 are unchanged unless separately confirmed.

- [ ] Every business input opened and row/page/file counts recorded, including remaining POD semantic audit.
- [ ] Original archive and separate attachments checked; unresolved omissions raised with client; actual replies or explicitly pending status recorded.
- [ ] Evidence-backed traps and cleaned-schema Mermaid ER available.
- [ ] Architecture proposal and Mermaid data/complaint flow available.
- [ ] Each of all five members has a substantive attributable commit.
- [ ] Required evidence merged into instructor `main`; a branch or draft question alone is insufficient.

## 4. Component implementation and acceptance

### A — extraction and retrieval

Implement email/guide parsing, POD OCR and rate-card extraction with original file locators, source hashes, parser/model versions, field uncertainty, visible failures and cached per-file processing outcomes. Do not equate a detected signature with recipient identity. Provide validated POD/rate records to B; expose `search_emails` and `search_policy` to C. Guide parsing remains conditional on receiving the guide; return unavailable policy honestly meanwhile. Ralph owns the full chunking → embedding/indexing → retrieval pipeline: define source-aware chunk boundaries/overlap, stable source/section or image locators, date/system metadata, embedding model/version, cache/incremental rebuild rules, metadata filtering and ranked retrieval. Compare relevant-source recall and citation accuracy on checkable queries; Jeffrey contributes realistic queries and business relevance judgments, while A/B/C verify factual expectations. Choose chunk sizes, retrieval settings and any reranking from measured examples rather than fixed guesses. Confirm class endpoint/embedding compatibility and cost first; FAISS is a candidate, not a requirement. If embeddings are unavailable or unjustified, document and evaluate a lexical alternative. SQL facts, identity joins and calculations stay in B’s tools rather than being indiscriminately embedded.

**Accept:** all assigned inputs have outcomes, retries are bounded, repeated extraction/embedding avoids duplicate paid work, index versions are reproducible, relevant sources are retrieved on owner-verified cases, and citations remain verifiable against original source locators.

### B — structured data, identity and analytics

Use Python/pandas for profiling and explicit, documented transformations; preserve raw records. Create cleaned keys using actual `(system_version, order_id)` and separate delivery-event keys. Preserve postal codes as text and raw timestamps with proven timezone assumptions. Build controlled rebuilds or keyed upserts, reconcile loaded/rejected/duplicate counts, use appropriate driver/time and source/order lookups, and integrate A's file-backed tools with locators and uncertainty. Current MySQL additions are the three case tables and two views; migrating A's evidence or other sources to SQL is future enhancement work.

Implement candidate lookup and `get_delivery_history`; integrate `get_pod`, `get_gps_window` and date-sensitive `get_rate` through validated SQL/file-backed adapters as appropriate. Preserve ambiguous candidates, absent records and query failures distinctly. Do not infer complete attempt history from the single event per order in this export or apply April pricing to earlier orders without authority.

After the cited complaint flow works, implement `weekly_complaints` using the approved case source, reporting week/timezone, deduplication and driver/zone definitions. Missing case log or zone mapping produces a labelled limitation; an email-based proxy requires explicit approval and must be clearly separate. Compile the one-page data quality report from all owners.

**Accept:** native MySQL counts and reruns reconcile; system identities remain distinct; calculations and weekly totals can be independently checked; unknown attribution is retained.

### C — API, agent, sessions and guardrails

Choose the Python framework and orchestration approach after capability checks. Own validated HTTP complaint/session/weekly routes and thin API error mapping, reusable service methods, deterministic input refusals, output PII/policy checks, question-time tool calls, candidate clarification, evidence reconciliation and final citation validation. Do not invent policy or default to a universal source hierarchy. LangGraph remains proposed until agreed.

Persist session IDs, messages, candidates, evidence references, conflicts, recommendations, citations, usage, errors and workflow status in ignored durable storage. Demonstrate a follow-up and restart recovery. Keep model keys server-side; handle timeouts, exceptions and bounded retries. Define trace IDs, latency/token/cost events, safe errors and replayable local traces; instrument model calls and provide a daily total without double-counting A's paid extraction. E helps consolidate verification, not model-cost arithmetic ownership.

**Accept:** React reaches the documented API; identity/policy uncertainty produces clarification or abstention; citations reference returned evidence; sessions survive restart; one unavailable dependency does not crash the application.

### D — React, business acceptance and presentation

Implement complaint entry, submit/loading/error/retry, resolved order or candidate clarification, evidence/conflicts, recommendation and visible source references. Support follow-ups using stable session IDs and show recovery after backend restart. Build the weekly driver/zone view with period selection and unknown attribution using B's result through C's API. Keep the UI recommendation-only and model keys out of browser code.

Use synthetic API examples while services develop. Jeffrey defines realistic complaint/clarification scenarios, reviews answer usefulness and understandable limitations, and helps Ralph assess retrieval relevance. A/B/C validate technical facts and policy support; Jeffrey does not author unsupported logistics rules. Contribute frontend checks, journey cases and sanitised screenshots; C owns backend/API work and E owns the shared runner/runbook.

Jeffrey owns the business-value narrative, five-minute pitch deck, demo storyline and client-facing presentation. Draft the storyline for Checkpoint 2 and rehearse a complete pitch on 24 Nov; refine it by 26 Nov. John supplies technical validation and technical Q&A, A/B supply evidence, and E supports timing/runbook/recovery. Choose and record the live application operator and backup at the 24 Nov rehearsal so Jeffrey can focus on presenting; do not assume the presenter must also operate the laptop. Keep deck preparation lightweight until the cited flow works.

**Accept:** normal, ambiguous, missing-source, refusal and retry journeys are usable; citations are accessible; weekly definitions/limitations are visible; lint/build and journey checks pass; the pitch is evidence-backed, timed to five minutes and consistent with actual capabilities.

### E — setup verification, evaluation and integration

Maintain the package checklist and setup confirmations; compare the original archive/attachments before reporting supplier omissions. Starting from C's starter, implement a local one-command eval runner with explicit expectations, owner/category and sanitised results. Separate refusal from missing-evidence abstention and HTTP success from a correct answer. A/B/C/D author and fix their cases.

Maintain the full-stack smoke checklist: startup order, health, React-to-API request, cited answer, clarification, unavailable dependency, follow-up and restart. Draft the demo runbook and collect verified evidence/screenshots with D. Add simple CI lint/build/synthetic checks only after the local runner is stable and C has reviewed the configuration. Do not put client data into CI.

**Accept:** a new teammate can follow setup/run steps; one command gives meaningful pass/fail; failures identify the responsible component; demo steps and recovery have been exercised, not merely written.

## 5. Contracts and handoffs

Freeze minimum contracts by 17 Nov, then version changes with consumers. Details and synthetic examples belong in [contracts](../02-Design/contracts.md).

| Contract/tool | Owner → consumer | Required behaviour |
|---|---|---|
| Extracted POD/rate records | A → B/C | Source hash/path, locator, system/order candidate, extracted fields, uncertainty/version/errors |
| Candidate lookup and SQL/GPS tools | B → C | Composite identity, safe filters, timezone provenance, data and cited source records |
| `search_policy`, `search_emails` | A → C | Applicable-date/context filters, source locators and unavailable-source response |
| `resolve_order` / complaint service | C using B → HTTP/React | Clarify ambiguous candidates; do not select a system without supporting evidence |
| Complaint/session HTTP API | C → D/E | Request/session IDs, status, candidates, evidence, conflicts, recommendation, citations and safe errors |
| Weekly HTTP API | B computes; C exposes → D/E | Week boundaries/timezone, source/dedup/attribution definitions, driver/zone totals and unknowns |
| Telemetry | C defines; A/B/C emit → E verifies | Trace IDs, tools, latency, model/tokens/cost, errors; no client text in committed traces |
| Eval cases/results | C supplies starter; E maintains; all contribute | Case/category/owner, input path or synthetic fixture, explicit expectations, source requirements, pass/fail |

Use result states `found`, `not_found`, `ambiguous`, `partial`, `failed`; define how `ok` relates to them. A successful empty query differs from a failing dependency. Citations include source ID/type/ref/locator and a source record key where relevant. Validate existence and claim support. Use actual `system_version`/`order_id` at the data boundary; map generic API names explicitly if used.

## 6. Evaluations and grading evidence

Target **26 checkable cases**, at least 20 passing before rehearsal, including at least two refusals and five kill-shot phrasings. All required acceptance, identity and refusal cases must pass; extra passing cases cannot conceal a critical failure. Start with five integrated cases on 18–19 Nov. Expected missing-policy abstention is not a substitute for a deterministic policy refusal. Case owners define expectations and fix failures; E operates and extends the runner with C's review.

| Contributor | Initial allocation | Focus |
|---|---:|---|
| A / Ralph | 5 | Retrieval, extraction uncertainty, missing images/policy |
| B / Jenn Fang | 6 | Identity, time, rates, postal handling, missing records and weekly definitions |
| C / John | 8 | Workflow/state/failure; five kill-shot phrasings, at least two of which are explicit refusals |
| D / Jeffrey | 3 | Realistic customer journeys, clarification and visible citations/errors; also reviews business relevance of A/E scenarios without duplicating case counts |
| E / Ho Wai Hong | 4 | API/smoke checks, restart and dependency failure with checkable content |

| Harness area | Required evidence | Owner/support |
|---|---|---|
| Grounding | Question-time tools and hard cross-source trace | C with A/B |
| Citations | Three cited answers including a conflict and reasoned trust | A/B provenance; C validates; D displays; E verifies |
| Guardrails | Code module, five phrasings, refusal evidence | C; E consolidates results |
| Error handling | Deliberately unavailable dependency; honest degradation | Each owner fixes; E/D capture safe evidence |
| State | Follow-up plus restart retaining session | C implements; D/E verify |
| Human approval | Explicit recommendation-only boundary, or gated execution if scope changes | C documents; D/E verify |
| Observability | Linked tools/latency/usage, replay example, cumulative spend | C/A/B instrument; E checks evidence |
| Evals | One command, ≥20 cases, ≥2 refusals, sanitised latest results and failure-to-fix history | E runner; all own cases/fixes |

Keep actual client-bearing inputs/results local; CI uses synthetic fixtures. Results are committed only after execution and sanitisation.

## 7. Milestones and ownership gates

| Date | Gate | Accountable outputs |
|---|---|---|
| 16–17 Nov | Release/setup, questions and contracts | A/B audit; E package/setup checks; C API/endpoint/runner starter; D journey/fixtures; Jeffrey helps frame questions; John validates/sends them |
| 17 Nov, 14:00 | Team sync | Confirm component boundaries, minimum stack and recommendation-only scope; review blockers and contracts |
| 18 Nov | Internal target | First thin React → C API/agent → cited evidence flow; E's first five cases runnable |
| 19 Nov | Internal audit/integration review | Cleaned ER, draft architecture, remaining source gaps and early image evidence; consult timing remains as separately scheduled |
| **20 Nov, 17:00** | **Checkpoint 1** | Audit/ER/traps/questions/architecture merged; all five contributors visible; owners per Section 3 |
| 20 Nov, before close | Internal Checkpoint 2 rehearsal | A image extraction → B cited record/tool → C answer → D UI; E runs smoke/evals; John checks spend. Protect this gate rather than assume weekend work. |
| **23 Nov, 09:00** | **Checkpoint 2** | Two source types including images, cited answer, OCR evidence and spend checked; A/B/C/D implement their layers, E verifies, Jeffrey drafts demo storyline, John confirms merged submission |
| 24 Nov, 10:00 | Rehearsal / Consult 4 | C complete workflow/guardrails/state; A/B evidence/aggregates; D UI; E ≥20 passing evals and recovery rehearsal; Jeffrey timed pitch; choose operator/backup; John validates technical claims |
| 26 Nov, 09:00–12:00 | Final sprint | A extraction limitations; B one-page quality report; C diagrams/backend recovery; D UI/screenshots and final pitch; E runbook/full-stack check; John technical validation/submission |
| 27 Nov, 09:00–13:00 | Live demo, SR902 | Jeffrey leads the 5-minute pitch and client-facing demo/Q&A; rehearsed operator handles UI; John leads technical Q&A; A/B explain evidence/data; E supports runbook/recovery and eval evidence. Five-minute demo plus panel questions. |

Do not shift other official deadlines or consults solely because Checkpoint 1 moved. During the daily check, report the last working end-to-end flow, failed checks, client blockers, dependencies and actual spend. If policy is still missing, demonstrate verified evidence and honest abstention; do not describe that as a completed policy-resolution feature.

## 8. Files and deliverables

| Path | Responsibility |
|---|---|
| `backend/` | C API/agent/runtime; A/B implement their source modules |
| `database/` | B cleaned schema/loaders/queries |
| `scripts/` | A/B loading/extraction instructions; E setup verification, C reviews runtime wiring |
| `frontend/` | D React and frontend checks |
| `evals/` | E runner and synthetic cases; C starter/review; all case owners |
| `docs/05-Reviews/` | A/B audit/traps; E package/checkpoint reconciliation; all provide evidence |
| `docs/00-Biz_Requirements/client_qa.md` | John validates/sends/logs; Jeffrey frames client wording; A/B supply source facts |
| `docs/02-Design/architecture.md` | C compiles architecture; A data-flow, B cleaned ER, C/D sequence contributions; at least two Mermaid diagrams |
| `docs/02-Design/contracts.md` | C coordinates; all consumers review |
| `docs/04-Testing_Evals/data_quality_report.md` | B compiles a one-page report; all contribute |
| `docs/06-Releases/demo_checklist.md` | E runbook/smoke; Jeffrey UI storyline, deck and pitch; C recovery/technical Q&A; John submission |
| `docs/06-Releases/retrospective.md` | All document limitations, tradeoffs and lessons |
| `docs/01-Plans_Status/Developer-A_tasklist.md` through `Developer-E_tasklist.md` | Each named owner updates status, evidence, next action and blockers |
| `data/`, `output/` | Ignored raw/derived data and runtime state; no client-bearing content in Git |

Preserve root instructor documents and their navigation. The team docs supplement them; use links to the current v0.5 plan and archived earlier versions, not obsolete paths. A placeholder or proposed output is not completed evidence.

## 9. Deployment and scope

Keep React and local laptop deployment for assessment. MySQL may run through the existing Compose service or a developer's installed local MySQL; all five use consistent schema and counts. No public hosting is required for the course. Confirm endpoint/network failure behaviour; local deployment still requires connectivity for remote LLM calls.

Keep Python logic independent of UI and secrets outside the browser. Post-course portfolio hosting is a separate phase using synthetic or explicitly approved data, separate credentials and budget; see [hosting options](../02-Design/hosting-options.md). Streamlit remains a team-decided contingency if frontend integration threatens the demo, not an additional application to build now.

## 10. Decisions and risks

Track owners/actions in [delivery RID](delivery_RID.md). Immediate items: missing case log/guide, applicable rate history, zone/service rules, GPS semantics, stack/endpoint capabilities and the load on the critical API/agent path. Draft questions are not sent questions; checklist completion requires actual evidence.

## 11. Version history

| Version | Date | Changes |
|---|---|---|
| Original–0.4 | 13–15 Nov 2026 | Earlier four-developer plans retained in `docs/Archive/` |
| 0.5 | 16 Nov 2026 | Released-package findings, five named owners, D focused on React, C API/agent ownership, bounded E setup/eval/integration deliverables, revised Checkpoint 1 and shared local setup; explicit Ralph retrieval pipeline and Jeffrey presentation/client-facing responsibilities |
