# Team 2 Plan — Merlion Express Capstone

**Version:** 0.3 *(Pre-Dataset Release and Project Brief)*

**Updated:** 14 Nov 2026, 12:43 SGT (UTC+08:00)

**Status:** DRAFT for team to review. Developer assignments and proposed design choices remain subject to team agreement.

**Team:** John Phang (Captain), Ralph, Jenn Fang, Jeffrey Kong

**Developer identifiers:** A, B, C and D. Assignment of people to roles is pending team confirmation.

**Next sync:** Tue 17 Nov 2026, 14:00 SGT. All times below are Singapore time.

## 1. Purpose, sources and current baseline

Deliver a complaint-triage assistant that identifies an order from an email, gathers delivery/POD/GPS/rate/policy evidence, reconciles conflicting sources, and recommends a resolution. Include a weekly view of complaints by driver and zone.

This revision supersedes the task strategy in v0.2. It explicitly plans EDA, initial loading, cleaning, repeatable loading, frontend implementation, integration and grading evidence for four developers.

### Authoritative sources

| Source | Purpose |
|---|---|
| `docs/00-Biz_Requirements/CLIENT_BRIEF.md` | Client outcomes, all-source ingestion, constraints and engagement rules |
| `docs/05-Reviews/HARNESS_CHECKLIST.md` | Eight grading areas and required evidence |
| `docs/05-Reviews/CHECKPOINTS.md` | Checkpoint dates and acceptance criteria; confirm instructor can find the moved file |
| `README.md`, `data/README.md` | Team contributions, data handling, setup and deliverables |
| NTU Capstone Submission repository | <https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express> |
| Team backup repository | <https://github.com/NTU-AIE1F-Team6/capstone-merlion-express> |

All work to be merged to course submission repository. Team backup repository is used in guide v0.3 for planning purposes before dataset release and project brief from course director.

Review baseline: team backup repository `main`, commit `c37d3a37f33d4178a44031659610f75ea7f12cdb`, checked on 14 Nov 2026. The original submission repository was not independently verified for this revision.

Team PR #1, “Add initial project scaffold”, merged on 13 Nov 2026 (to Team Repo). React 19/Vite 8 scaffolding exists under `frontend/`; it currently contains starter UI. `backend/`, `database/`, `scripts/`, `evals/` and `docs/` contain placeholders. MySQL 8 is configured in `docker-compose.yml`. No backend framework, LangGraph implementation, retrieval index or evaluation runner is implemented in this baseline.

The data package and project brief is expected at the 16 Nov briefing. Counts and schemas in this plan come from the brief and must be verified against the actual package. The absence of client data from git is expected.

### Constraints to carry into implementation

- Use the class-provided LLM API endpoint. No other paid AI services. Confirm vision and embedding capabilities, pricing and permitted local OCR/embedding options before full processing.
- Ingest all required source types: SQL, tabular, images and documents; also process the GPS JSONL source named in the manifest.
- Retrieve facts through tools at question time. Cross-source linkage and calculations are performed by code.
- Cite source tables, files or images; identify contradictions, missing evidence and unresolved identity explicitly.
- Keep client data, keys, detailed traces, OCR output, indexes and checkpoints out of git. Commit sanitised evidence and aggregate eval results.
- Each member commits substantive work under their own GitHub identity. Use co-author attribution when pairing.

## 2. Delivery strategy and workload balance

Assign ownership by deliverable, with two data owners, one backend/agent owner and one frontend/integration-quality owner. Every owner implements the tests, error handling, provenance and instrumentation for their component. Quality is built throughout the project.

### Deliverables Ownership

| Developer | Primary ownership | Secondary responsibility | Main dependency supplied |
|---|---|---|---|
| A | Unstructured-source EDA, extraction/OCR and text retrieval | Source-specific tests/evals, policy evidence and citation provenance | Cited search results and extracted POD/rate records for B/C |
| B | Structured-source EDA, cleaned schema, loaders, order-candidate lookup and SQL tools | Data-integrity checks and weekly analytics after the first cited complaint flow | Candidate orders, cited data tools and weekly counts for C/D |
| C | Agent services, sessions and guardrails | Final-answer citation checks and shared model telemetry | Stable backend service, clarification workflow and persistent sessions behind D’s routes |
| D | React frontend, thin HTTP API, integration verification and shared eval runner | Request/response models, CI checks and demo runbook; each owner supplies cases | Usable UI, repeatable integrated checks and demo readiness |

### Coordination Responsibilities

These coordination duties should remain small and use existing component outputs.

| Developer | Responsibilities |
| :-: | --- |
| A,B | instrument their tools using C's shared logging contract. |
| C | owns service orchestration, final-answer guardrails and backend/model telemetry; D owns HTTP routes and A/B own source checks. |
| D | owns HTTP routes/models, React, eval runner and integration/CI checks; every owner supplies and fixes component cases. |
| Captain | coordinates client communication, pitch and submission readiness; A/B draft source questions. |
| ALL | all four own fixes in their respective components. |
| ALL | Each developer documents their own design and audit findings. |
| B | compiles the data quality report from all owners’ findings. |
| C | compiles architecture documentation; A/B/D contribute source and UI evidence. |
| D | supplies UI screenshots and demo steps; Captain coordinates the pitch and overall rehearsal. |

### Working rules

1. Pull the merged scaffold before branching. Use short-lived `feature/<description>` branches and reviewable PRs.
2. Agree minimum API/tool schemas early, then evolve them with the affected owner. D develops against synthetic responses while C implements the service.
3. EDA gates decisions about each source; it does not prevent UI, API, logging and eval scaffolding from progressing.
4. Integrate daily. Demonstrate one complete complaint flow before broadening all features.
5. If a component is blocked, publish its expected contract and a synthetic fixture; log the missing evidence or client decision.
6. Review workload daily. Reassign a bounded task when one developer becomes a bottleneck; record the new owner.

## 3. Stage 1 — EDA and initial loading, 16–19 Nov

EDA and loading are distinct but iterative. Preserve raw files; load working copies where needed for profiling. A successful import does not imply that the data is clean or linked correctly.

| Developer | EDA and initial-load tasks | Outputs by Checkpoint 1 |
|---|---|---|
| A | Inventory every POD image, rate card, complaint email and policy/guide document assigned to this stream. Open all files; record file/page counts. Sample OCR/extraction, assess readability and document structure, identify missing PODs and uncertain fields. Check guide presence jointly with B. | Unstructured audit section; extraction samples retained locally; processing manifest design; retrieval/provenance contract; traps and client questions |
| B | Import the SQL dump; inspect all tables and case-log/guide tabular files; profile GPS JSONL. Record counts, keys, nulls, duplicates, parse failures and join coverage. Investigate migration overlap, postal codes and timezone offsets. | Structured audit; repeatable raw import; cleaned ER; candidate-order identity rules; traps and client questions |
| C | Agree how B returns candidate orders and how A/B return evidence and errors. Define service, clarification and session behaviour with D; create a backend shell and endpoint smoke test after key release. | Architecture proposal; initial API contract and synthetic fixture; clarification rules; endpoint capability/budget findings |
| D | Map client journeys into screens, build complaint input and thin HTTP routes using synthetic service responses, define weekly fields with B, and create the initial eval runner and integration smoke check. | React/API mock flow; runnable eval cases; UI acceptance checklist; missing-evidence/clarification states |

### Package reconciliation

Use the following as the expected manifest, all beneath local `data/`:

| Source | Expected content from brief | Audit owner |
|---|---|---|
| `data/sql/merlion_ops.sql` | Operations SQL dump with legacy/new-system order evidence | B |
| `data/tabular/` | CS case log and Resolution Guide | B inventories; A handles document retrieval if appropriate |
| `data/logs/gps_pings_sample.jsonl` | Approximately 60,000 GPS pings | B |
| `data/images/proof_of_delivery/` | 80 POD scans | A |
| `data/images/rate_cards/` | Rate-card images | A |
| `data/docs/complaint_emails/` | 90 complaint emails | A |

Exact filenames, counts and guide format must be confirmed. If the guide is tabular, B loads its records and A/C consume the agreed representation; do not assume a document format or invent missing policy.

Every supplied file must be opened and accounted for. Audit evidence records counts, parse status, source identifiers and decisions without copying client records into git. Investigate timestamp offsets empirically before normalising; retain raw timestamps and timezone assumptions. Preserve postal codes as text and flag unrecoverable values rather than inventing digits. Confirm whether `(source_system, order_no)` is unique at order level; delivery events may require a separate event key.

Raise missing-package questions promptly on 16–17 Nov because replies take up to two working days. Captain sends questions to the course director with subject `Client question — Team 2`. Each source owner drafts precise questions; log questions, dates, status, answers and resulting decisions in `docs/00-Biz_Requirements/client_qa.md`.

### Checkpoint 1 — Thu 19 Nov, 09:00

- [ ] Every file opened; row/page/file counts recorded in `docs/05-Reviews/data_audit.md`.
- [ ] Package checked against the brief in `docs/05-Reviews/package_checklist.md`; missing items raised with client and answers recorded when received. Mark pending replies explicitly and raise timing risk at the consult.
- [ ] Evidence-backed trap list in `docs/05-Reviews/trap_list.md`.
- [ ] Cleaned-schema ER diagram and architecture proposal in `docs/02-Design/architecture.md`.
- [ ] Every member has committed substantive work under their own account.

**Checkpoint 1 owners (role assignments, not person assignments):**

| Role | Accountable output by 19 Nov, 09:00 SGT |
|---|---|
| A | Open and inventory every image, complaint email and guide/policy file; record counts, unreadable files, source traps and questions in the audit and package checklist. |
| B | Open and profile every SQL, tabular and GPS file; record row counts, join risks and traps; produce the cleaned-schema ER diagram. |
| C | Compile the architecture proposal and Mermaid data/complaint flow with A/B evidence; publish minimum service/tool and citation contracts. |
| D | Show a synthetic React → HTTP route → service flow, clarification/missing-evidence states and the initial runnable eval cases. |
| Captain | Consolidate package-versus-brief gaps, send client questions, maintain the client Q&A and verify checkpoint evidence is merged into instructor `main`. |
| All roles | Make a substantive commit under each developer’s own account and review cross-role handoffs. |

## 4. Stage 2 — Implement owned components

### A — Extraction, loading and retrieval

1. Implement parsers for emails and policy/guide documents, preserving source path and locators.
2. Build POD OCR/extraction for order reference, timestamp, recipient and signature presence where observable. Record uncertainty; do not treat a detected signature as proof of recipient identity.
3. Extract rate cards with service, zone, weight band, price, currency and validity/version information where present.
4. Maintain a per-file processing manifest: source ID/hash, parser/model version, status, errors and cache location. Cache completed extraction; rerun changed or failed inputs deliberately.
5. Provide validated POD/rate records to B through an agreed schema. Retain links to the original image and extraction uncertainty.
6. Chunk/embed searchable text only where useful; retain stable source locators and retrieval metadata. Implement `search_policy` and `search_emails`.
7. Confirm endpoint and embedding compatibility before selecting a vector store. FAISS is a candidate, not a mandated choice.
8. Add extraction/retrieval tests, bounded retries, honest unavailable-source results and tool telemetry.

Acceptance: every assigned input has a processing outcome; failures are visible; cached runs avoid duplicate paid work; search results cite verifiable sources; POD/rate records can be loaded by B.

### B — Data model, loaders, SQL tools and analytics

1. Implement repeatable raw import and transformations for SQL, tabular and GPS sources. Document the order of commands.
2. Create cleaned tables with validated source-system/order linkage, delivery-event keys, timestamp provenance and postal-code treatment; expose candidate-order lookup using available date/name/address evidence without collapsing v1/v2 identities.
3. Load A's extracted POD/rate records with their source references and uncertainty. Agree a handoff sample early so the loader can be tested before full OCR finishes.
4. Make reruns idempotent through explicit keys/upserts or controlled rebuilds. Reconcile source, loaded, rejected and duplicate counts.
5. Implement `get_delivery_history`, `get_pod`, `get_gps_window` and `get_rate`. Date-sensitive rate queries must select the applicable version.
6. After one cited complaint flow works, implement `weekly_complaints`: driver/zone counts, reporting period, attribution rules and handling of unresolved orders. Report unknown attribution rather than dropping it silently. Agree which source defines a complaint and how duplicate complaints are treated.
7. Index relevant order/source and GPS driver/time lookups. Keep joins and numeric calculations in code/SQL.
8. Add data-integrity and aggregate checks, caught errors and tool telemetry. Compile the one-page data quality report from all owners' findings.

Acceptance: counts reconcile; candidate lookup does not merge unrelated v1/v2 orders; reruns do not duplicate records; tools return citations and honest errors; weekly results can be independently checked.

### C — Agent service and runtime harness

1. Agree the Python framework and service-to-route contract with D. Implement complaint/session and weekly-summary service methods behind D’s HTTP routes.
2. Consume B’s candidate-order lookup; present candidates and ask for clarification when identity remains unresolved. Never guess a source system.
3. Orchestrate resolve order → gather evidence → reconcile → recommend per policy → validate and respond. LangGraph is proposed, subject to team agreement and compatibility.
4. Query tools at question time and preserve evidence provenance. Separate policy rules/calculations from generated explanation; unsupported recommendations must be withheld.
5. Implement persistent sessions/checkpointing, stable session IDs and restart recovery. Persist clarifications and evidence references safely.
6. Implement deterministic input refusal rules and code-based output checks for PII/policy violations. Validate final-answer citations against A/B source references; A/B own provenance at their tool boundaries, while case-specific evals assess claim support.
7. Define the minimal shared telemetry contract and instrument backend/model calls; A/B instrument their own tools and paid extraction. Combine usage once for a daily spend figure, avoiding double counting.
8. Protect the API key in backend services. Agree error mapping with D; add backend timeouts, exception handling and bounded retries where appropriate.
9. Document backend startup and recovery commands and supply a trace for the demo; D documents UI steps, while Captain coordinates the overall rehearsal and pitch.

Proposed MVP boundary: recommend re-delivery/refund/compensation/rejection; do not execute payments, operational updates or outbound messages. Record this explicitly in architecture documentation. The harness permits consequential actions to be excluded. If the team includes execution, add an approval gate, approver decision, durable resume and duplicate-execution protection, and demonstrate it.

Acceptance: React can call the service; a full complaint produces grounded evidence and citations; ambiguous/missing/conflicting evidence is handled; refusals work; follow-ups survive restart; one bad dependency does not crash the app.

### D — Frontend, HTTP API, integration and evaluation

1. Extend the existing React/Vite scaffold with a small complaint workspace: email input, submission, loading, error and retry states.
2. Display resolved order or candidate clarification, evidence, source conflicts, recommendation and visible source references.
3. Support follow-up questions and the persisted session ID. Demonstrate UI recovery after backend restart.
4. Build the weekly driver/zone view using B's aggregate through C's service and D's HTTP route, with reporting-period selection and unknown-attribution display.
5. Add approval UI only if execution enters scope. For recommendation-only MVP, make that boundary clear in the interface.
6. Implement thin complaint/session and weekly-summary HTTP routes with validated request/response models around C’s services. Own route errors and React connectivity; C reviews the service boundary.
7. Build a single-command eval runner and consolidated results. Collect component-owned cases from A/B/C; each owner fixes failures in their area. Add automated lint/build/eval checks in CI if repository permissions allow them.
8. Own repeatable end-to-end integration checks from React through API to synthetic or approved evidence. Cover normal, ambiguous, unavailable-source, refusal and malformed responses; supply sanitised UI screenshots to the Captain.
9. Own the demo runbook and full-stack smoke test with C: startup order, health checks, restart/recovery and fallback steps. Captain coordinates the pitch and submission.

Acceptance: React reaches C’s service through D’s validated HTTP routes; complaint and weekly workflows are usable; citations and conflicts are visible; errors/clarifications do not dead-end; the browser never receives the model API key; shared eval and integration smoke checks produce checkable pass/fail output.

### Protecting capacity

- C owns orchestration, state, final-answer guardrails and backend/model telemetry. A/B own source provenance, source-specific retries and tool telemetry; B owns candidate lookup. D owns React, thin HTTP routes/models, eval runner and cross-component verification.
- A/B own ingestion validation and source-specific eval cases. C owns workflow, state and refusal cases. D owns UI cases and runner integration; each owner fixes failures in their component.
- Keep UI scope to complaint triage and the required weekly view. Defer authentication systems, elaborate dashboards and extra operational workflows unless essential to agreed requirements.
- Preserve the one-page report, architecture diagrams, pitch and honest post-mortem as shared deliverables. B compiles the report; C compiles architecture; Captain coordinates pitch and submission; D owns the demo runbook and integrated smoke check.

## 5. Contracts and handoffs

Freeze minimum contracts by 17 Nov. Use typed models or JSON Schema, sample success/failure responses and synthetic fixtures; record changes in `docs/02-Design/contracts.md`.

| Contract | Owner | Consumer | Minimum fields/behaviour |
|---|---|---|---|
| Extracted POD/rate records | A + B agree; A produces | B | Stable source ID, image locator, extracted fields, uncertainty, extraction version/status |
| Cleaned data model and candidate lookup | B | A/C | Order identity, event identity, candidate evidence, time semantics, source provenance and join rules |
| Retrieval/SQL tool results | A/B | C | Success/missing/ambiguous/failure outcome, data, verifiable source references and structured error |
| Complaint/session HTTP API | D implements routes/models; C agrees service contract | React | Request/session IDs, workflow status, candidates, evidence, conflicts, recommendation, citations and errors |
| Weekly-summary HTTP API | B computes; C supplies service; D exposes route | React | Period boundaries/timezone, driver/zone aggregates, unknown attribution and definitions |
| Telemetry | C defines; A/B/C emit | All; D verifies | Linked trace events, latency, tokens/cost, source references and errors; no client data in committed logs |
| Eval format | D defines; all contribute | Runner | Case ID, category, input, checkable expectations, required sources, owner and outcome |

### Proposed tool signatures

| Tool | Input | Owner |
|---|---|---|
| `resolve_order` | Email text plus optional clarification | C orchestrates; B supplies candidate lookup and identity evidence |
| `get_delivery_history` | source_system, order_no | B |
| `get_pod` | source_system, order_no | B, using A's extraction |
| `get_gps_window` | driver_id, start_time, end_time, explicit timezone semantics | B |
| `get_rate` | service, zone, weight, applicable_date; refine after schema audit | B, using A's extraction |
| `search_policy` | query, optional effective_date/context filters | A |
| `search_emails` | query, optional order/source filters | A |
| `weekly_complaints` | week_start, agreed reporting timezone | B |

Common result example:

```json
{
  "ok": true,
  "status": "found",
  "data": {},
  "sources": [],
  "error": null
}
```

Define `status` values such as `found`, `not_found`, `ambiguous`, `partial` and `failed`; define how `ok` relates to them. A successful query returning no record is distinct from a failed dependency. Structured errors include code, safe message and retryability.

Citation example:

```json
{
  "source_id": "stable-source-id",
  "type": "image",
  "ref": "data/images/proof_of_delivery/example.png",
  "locator": "page/region or extraction field",
  "record_key": null
}
```

Use actual row keys, document positions or image locators at runtime. Check that references exist. Keep original evidence available locally to verify citations; sanitise anything committed.

Proposed persisted state: `session_id`, `messages`, `email_text`, `order_candidates`, `order`, `evidence`, `conflicts`, `recommendation`, `citations`, `usage`, `errors`, `workflow_status`; add approval state only if execution is included.

## 6. Evaluation and grading evidence

Target at least 24 checkable cases for a buffer above the required 20. Start with five cases during the first integration, then grow continuously. All required cases must pass before rehearsal; a pass requires checking the answer/evidence, not only successful HTTP delivery.

| Contributor | Suggested case allocation | Focus |
|---|---|---|
| A | 6 | Document retrieval, guide evidence, OCR uncertainty and missing/unreadable images |
| B | 6 | Duplicate order IDs, GPS/timezone, rate version, postal-code issues and weekly aggregates |
| C | 8 | Workflow, ambiguity, contradiction, persistence, failure handling and five kill-shot phrasings; include at least two refusal cases |
| D | 4 | Integrated complaint/weekly journeys, clarification and visible citations/errors |

Cases may exercise several layers. Refine the allocation when the actual traps are known. Include normal questions and expected abstention due to missing evidence as well as policy refusals. Each developer must rerun the relevant cases after changes and the shared suite before integration. Commit sanitised latest results and fixes; keep client-bearing inputs and detailed outputs local. The runner must accept local data/fixture paths.

| Harness area | Evidence required before demo | Responsible owner/support |
|---|---|---|
| Grounding | Tool definitions and trace of a hard cross-source question, retrieved at question time | C with A/B |
| Citations | Three visible cited answers, including a conflict and why a source is trusted | A/B provide provenance; C checks final answer; D captures UI evidence |
| Guardrails | Code module; five kill-shot phrasings tested; refusal evidence | C implements; D runs suite |
| Error handling | Disable a dependency deliberately; app degrades honestly; sanitised screenshot | Component owner fixes; D captures |
| State | Follow-up question and restart mid-conversation with preserved session | C implements; D verifies |
| Human approval | Document recommendation-only boundary, or demonstrate gated execution if included | C documents; D verifies |
| Observability | Linked trace, replay/diagnosis example and cumulative API spend | C instruments backend/model; A/B instrument tools and extraction; Captain checks daily total |
| Evals | At least 20 cases, at least two refusals, one command, latest committed results and failure-to-fix history | D builds runner and CI integration; A/B/C/D contribute and fix their cases |

Agree conflict-resolution rules from evidence/client answers; do not create a universal hierarchy such as “GPS always overrides POD”. Missing policy produces a stated limitation and client question, not invented compensation terms.

## 7. Milestones and integration gates

Official checkpoint requirements are distinguished below from additional team targets.

| Date | Official event | Team target and integration gate |
|---|---|---|
| Mon 16 Nov | Briefing; package/key expected | A/B inventory and initial imports; confirm endpoint capabilities; C backend shell; D React mock flow; raise missing items immediately |
| Tue 17 Nov, 14:00 | Team sync | Confirm named owners, MVP boundaries and contracts; sample A→B extraction handoff; connect React to backend using synthetic responses; client questions sent |
| Wed 18 Nov | Internal target | One thin complaint flow from React through D’s route and C’s service to loaded evidence and cited response; first five evals runnable |
| Thu 19 Nov, 09:00 | Checkpoint 1; Consult 1 at 10:00 | Audit, cleaned ER, traps, package reconciliation/client Q&A, architecture proposal, substantive commit from all four |
| Fri 20 Nov | Consult 2 | Grow source coverage and integration; prioritise one cited complaint flow; start weekly aggregate/API/UI once that flow works; track blockers for remaining source types |
| Mon 23 Nov, 09:00 | Checkpoint 2; Consult 3 at 13:00 | Official: two source types end to end including images; cited answer; OCR extraction; spend checked. Internal targets: broaden source coverage, weekly view and runnable eval suite after the cited flow is stable |
| Tue 24 Nov, 10:00 | Consult 4; rehearsal; slot order announced | Full agent/tool workflow, code guardrails and 20+ passing evals; rehearse with working UI; identify remaining hardening defects |
| Thu 26 Nov, 09:00–12:00 | Final sprint | Final report, sanitised evidence, hostile rehearsal, timed pitch, restart/failure exercises and submission readiness |
| Fri 27 Nov, 09:00–13:00 | Demo, NTU@one-north SR902 | Per team: 5-minute pitch, 5-minute live demo and Q&A; bring laptop and charger |


### Checkpoint 2 ownership — Mon 23 Nov, 09:00 SGT

| Role | Accountable output |
|---|---|
| A | Working image OCR/extraction with source locators and uncertainty; one image-derived evidence handoff to B/C. |
| B | Repeatable load and cited SQL/data tools for at least one structured source, linked to A’s extracted record where needed. |
| C | Question-time workflow that combines the two source types and produces one grounded, cited answer; show model/tool trace and spend from backend calls. |
| D | Demonstrate the answer in React through validated HTTP routes; run the shared eval command and an integrated smoke check. |
| Captain | Confirm the two-source demonstration includes images, check cumulative API spend against budget, and verify the deliverables are merged into instructor `main`. |

### Demo hardening ownership — Tue 24 Nov rehearsal

| Role | Accountable output |
|---|---|
| A | Extraction/retrieval failure tests, cited source evidence and uncertainty handling. |
| B | Data-integrity, identity and weekly-aggregate checks; independently verifiable numbers. |
| C | Agent/tool workflow, code guardrails, persistent sessions, honest failure behaviour and trace replay. |
| D | At least 20 consolidated passing eval cases with A/B/C contributions, UI/API failure and restart checks, and the rehearsal runbook. |
| Captain | Run a timed rehearsal, assign fixes for failures and track remaining risks in the RID log. |

### Final sprint ownership — Thu 26 Nov, 09:00–12:00 SGT

| Role | Accountable output |
|---|---|
| A | Final source coverage, extraction limitations and sanitised citation examples. |
| B | One-page data quality report, reconciled counts and cleaned-schema explanation. |
| C | Final architecture diagrams, guardrail/session evidence and backend recovery steps. |
| D | Final UI, full-stack smoke check, demo runbook, sanitised screenshots and restart/failure rehearsal. |
| Captain | Confirm submission state, coordinate the five-minute pitch and lead the hostile-question rehearsal. |

### Client demo ownership — Fri 27 Nov, 09:00–13:00 SGT

| Role | Live responsibility |
|---|---|
| Captain | Lead the five-minute pitch, hand off to the live demo, manage time and coordinate Q&A. |
| D | Operate the application and weekly view; show citations, clarification and fallback behaviour using the runbook. |
| C | Explain orchestration, guardrails, state, model spend and what the app does when evidence or a dependency is unavailable. |
| B | Explain order identity, cleaned data, GPS/timezone handling, weekly counts and the data quality report. |
| A | Explain OCR/extraction, policy/email retrieval, source citations and uncertainty in images or documents. |
| All roles | Answer questions in their area honestly; do not invent a missing source or policy. |

Run a short daily integration check: what now works end to end, which interface/data decision blocks progress, failing evals and API spend. Resolve new dependencies with the affected developer the same day.

## 8. Project files and storage

Use the current documentation scaffold on `chore/PM_Scaffolding`. Its files are presently uncommitted; these paths become shared only after review and merge. The paths below are proposed responsibilities and do not imply that placeholder documents contain completed evidence.

```text
.
├── backend
├── data
│   └── README.md
├── database
├── docker-compose.yml
├── docs
│   ├── 00-Biz_Requirements
│   │   ├── CLIENT_BRIEF.md
│   │   └── client_qa.md
│   ├── 01-Plans_Status
│   │   ├── Capstone_TEAM_PLAN_v0.3.md
│   │   ├── delivery_RID.md
│   │   └── Name-A_tasklist.md
│   ├── 02-Design
│   │   ├── architecture.md
│   │   └── contracts.md
│   ├── 03-Handoffs
│   │   └── Name_YYYY-MM-DD-topic.md
│   ├── 04-Testing_Evals
│   │   └── data_quality_report.md
│   ├── 05-Reviews
│   │   ├── CHECKPOINTS.md
│   │   ├── data_audit.md
│   │   ├── HARNESS_CHECKLIST.md
│   │   ├── package_checklist.md
│   │   └── trap_list.md
│   ├── 06-Releases
│   │   ├── demo_checklist.md
│   │   └── retrospective.md
│   ├── Archive
│   │   ├── Capstone_TEAM_PLAN_ v0.2.md
│   │   └── TEAM_PLAN.md
│   └── README.md
├── evals
├── frontend
│   ├── eslint.config.js
│   ├── index.html
│   ├── node_modules
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   ├── README.md
│   ├── src
│   └── vite.config.js
├── output
├── README.md
└── scripts
```

| Path | Purpose | Owner |
|---|---|---|
| `backend/` | API, agent workflow, retrieval adapters, guardrails and logging | C coordinates; A/B own their modules |
| `database/` | Cleaned schema, migrations and SQL queries | B |
| `scripts/` | Repeatable import/extraction/load/setup commands | A/B; C integrates commands |
| `frontend/` | React complaint and weekly views | D |
| `evals/` | Executable runner and sanitised cases; plans and human-readable results go in `docs/04-Testing_Evals/` | D builds runner; all contribute cases and fixes |
| `docs/05-Reviews/data_audit.md` | Counts, source coverage, parsing and join findings | A/B sections; C/D contribute |
| `docs/05-Reviews/trap_list.md` | Evidence, decisions, unresolved assumptions and regression cases | All |
| `docs/05-Reviews/package_checklist.md` | Expected-versus-received package manifest | A/B |
| `docs/00-Biz_Requirements/client_qa.md` | Dated questions, answers and decisions | Captain coordinates; source owners draft |
| `docs/02-Design/architecture.md` | Architecture plus Mermaid data flow, cleaned ER and complaint sequence | C compiles; A/B/D supply their areas |
| `docs/02-Design/contracts.md` | API/tool/extraction/telemetry/eval contracts | C coordinates; all agree |
| `docs/04-Testing_Evals/data_quality_report.md` | One-page report of data problems and handling | B compiles; all contribute |
| `docs/06-Releases/demo_checklist.md` | Demo order, grading evidence, fallback procedure and submission checks | D owns runbook and smoke check; Captain coordinates pitch/submission; all contribute |
| `docs/06-Releases/retrospective.md` | Honest limitations, tradeoffs and lessons | All |
| `docs/README.md` | Accurate index and status of capstone documents | Captain coordinates |
| `docs/01-Plans_Status/` | Current plan, role task lists and decision log | Captain coordinates; each owner updates their tasks |
| `docs/03-Handoffs/` | Cross-owner handoff notes with PR, checks and remaining gaps | Sending owner |
| `docs/05-Reviews/` | Checkpoint and harness lists plus review/audit evidence | All |
| `data/` | Original client package; excluded from git except its README | A/B |
| `output/` | Local extraction caches, indexes, detailed traces/reports and runtime state as configured; excluded from git | Each producer |

The current plan is `docs/01-Plans_Status/Capstone_TEAM_PLAN_v0.3.md`; the earlier v0.2 plan is in `docs/Archive/`. `docs/README.md` is the navigation index and must list the actual paths and status of this capstone's documents. `docs/01-Plans_Status/Name-A_tasklist.md` is a task-list template; create one named file per developer for high-level ownership and link delivered work to PRs/evidence. Put decisions in `docs/01-Plans_Status/delivery_RID.md`, cross-owner handoffs in `docs/03-Handoffs/`, and reviews in `docs/05-Reviews/`. Daily documentation updates may use docs-only PRs; unfinished code remains on separate feature branches. Keep the official checkpoint checklist current.

The root `README.md` still links to `CLIENT_BRIEF.md`, while the new scaffold moves that file and `CHECKPOINTS.md` and `HARNESS_CHECKLIST.md` into `docs/`. Before merging this scaffold, update the root navigation or retain root copies/redirects, and verify the instructor's checkpoint review process accepts the chosen location. Do not silently break the course's documented entry points.

Ensure new artefact paths are covered by ignore rules. The current ignore rules cover `data/*`, `.env`, local DB/SQLite files, `faiss_*`, `output/` and frontend build/dependency directories. Do not assume all future cache formats are automatically excluded. Record only sanitised grading evidence outside ignored paths.

At least two Mermaid diagrams are required alongside the architecture documentation. Plan three useful diagrams: ingestion/data flow (A), cleaned ER (B), complaint sequence including React/API/tools/state (C with D).

## 9. Tech stack and deployment decision

**Recommendation (pending the 16 Nov briefing):** Lean toward **React**, use local deployment for the assessed demo, and defer the cloud hosting choice until the team knows the package size, data permissions and endpoint access on 16 Nov. The existing React 19/Vite 8 scaffold remains the frontend baseline. The backend framework, orchestration library, OCR method and vector store remain team decisions after a small capability and data check; MySQL 8 is already configured locally.

Design the application so the same source and container setup can later support a portfolio site. This is a portability target, not a commitment to host the course data or use a particular cloud provider. Keep ingestion, SQL queries, retrieval, citations and guardrails in Python services behind an API; the browser must not receive the LLM key. Use MySQL for structured records and calculations. Use searchable text retrieval only where it helps, with stable source locators; do not assume every source should be embedded.

| Component | Assessed course demo | Later portfolio site |
|---|---|---|
| Frontend | React/Vite on the demo laptop | The same React build served over HTTPS |
| Backend | Python API and application services on the demo laptop | The same service in a hosted container |
| Database | Local MySQL 8 in Docker with a persistent volume and course data | Separate hosted MySQL with synthetic or explicitly approved data |
| Retrieval and generated files | Local, ignored indexes, extraction cache and traces | Separate persistent storage rebuilt from portfolio-safe data |
| LLM access | Class-provided endpoint and team key, subject to confirmed capabilities and budget | Separately permitted credentials and budget, or a clearly labelled sample mode |
| Configuration | Local secrets outside Git; reproducible startup and recovery commands | Hosting secrets outside Git; backup, restart and access configuration |

Streamlit remains a fallback if React/API integration threatens the course schedule. It can connect to MySQL locally or in a container, but a hosted Streamlit app needs a reachable database and persistent storage outside the local demo laptop. Switching frontend frameworks requires a team decision because it changes D's work and the API/UI handoff. Do not publish the client package, extracted evidence or class key in a portfolio deployment without explicit permission.

## 10. Decisions and risks to close

Track delivery risks, issues, decisions and their outcomes in the [delivery RID log](delivery_RID.md).

## 11. Version history

| Version | Date | Changes |
|---|---|---|
| TEAM_PLAN.md | 13 Nov 2026 | Original consolidated draft from Jeffrey |
| 0.2 | 13 Nov 2026 | shared data foundation and workstreams A–D |
| 0.3 | 14–15 Nov 2026 | Initial plan, then rebalanced ownership: B candidate lookup, A/B source provenance, C orchestration and final checks, D UI, HTTP routes and eval runner; Captain coordinates pitch and submission. Person-to-role assignments remain unconfirmed. |
