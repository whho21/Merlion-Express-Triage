# Capstone API catalog

- **Version:** 0.9.0
- **Updated:** 17 Nov 2026 (SGT). 
- **Status:** draft design specification; HTTP routes and new service signatures require implementation and contract agreement.

One Python HTTP API connects the React screens to internal SQL, file-backed evidence and RAG services. Existing Python tools are identified separately from proposed interfaces; this document does not claim the backend or demo acceptance checks are complete.

## 1. Scope and conventions

| Boundary | Release design |
|---|---|
| Browser → backend | Six JSON endpoints under `/api`; one API service. FastAPI + Pydantic + Uvicorn is the recommended implementation stack, not an installed or frozen dependency choice. |
| Backend → data services | Python function calls for identity, SQL/GPS, evidence retrieval, rates and policy. Internal tools are not additional browser endpoints. |
| Preparation | Separate commands for initial database creation/seeding, case transformation, image/text ingestion and index publication. HTTP requests never trigger dataset reloads or paid image extraction. |
| Storage | MySQL operational/case tables and weekly views; four JSONL evidence files; GPS/reference files; optional semantic index; proposed local SQLite sessions. |
| Deployment | Local assessed demo. Authentication is not implemented; session IDs identify conversations, not authenticated users. Public access and user-access controls require a separate design. |
| Effects | Recommendations only. No refund execution, customer messaging, operational edits, arbitrary SQL endpoint or ingestion/upload/admin API. Saving conversation state does not create a canonical complaint in weekly reporting. |

- Requests/responses use JSON and UTF-8. Public order identity is `{system_version: "v1" | "v2", order_id: integer}`; an order number alone is not unique.
- Calendar dates use `YYYY-MM-DD`; timestamps carry explicit offsets/UTC. Reporting uses `Asia/Singapore`. Money is calculated using decimal arithmetic; JSON amounts are SGD numbers or `null` when unknown.
- Each request has a server-generated `request_id`; complaint workflows also have an opaque `session_id`. A request ID is a trace identifier, not an idempotency guarantee.
- Text sent to embedding/answer models and browser responses is minimised/masked. Restricted original evidence remains local; personal names need coverage beyond the existing regex helper.
- Existing source records may use `source_system`; adapters map it to `system_version` in public identities/citation keys without rewriting source IDs or locators.
- Raw/derived evidence, extraction caches, indexes, traces and sessions stay under git-ignored local paths. Share unmasked outputs privately; commit only synthetic API examples/fixtures. No model key belongs in `VITE_` variables.

## 2. HTTP endpoint catalog

All six HTTP handlers are **proposed**, with no HTTP server found in the reviewed checkout. Five have frontend call functions; health is declared in the route map but has no current screen caller.

| ID | Method and path | Request | Response / purpose |
|---|---|---|---|
| HTTP-01 | `POST /api/complaints` | `{email_text, session_id?}` | `ComplaintResult`; start triage, resolve candidates, gather evidence and recommend/clarify/abstain. |
| HTTP-02 | `POST /api/sessions/{session_id}/messages` | `{message?, selected_candidate?}` | `ComplaintResult`; continue the same complaint or select a candidate. |
| HTTP-03 | `GET /api/sessions/{session_id}` | Path session ID | `ComplaintResult` plus `messages`, `recovered: true`; recover saved state. |
| HTTP-04 | `GET /api/weekly/weeks` | None | `{weeks: string[], timezone: "Asia/Singapore", synthetic?: boolean}`; ascending available week starts. |
| HTTP-05 | `GET /api/weekly?week_start=YYYY-MM-DD` | Required query date | `WeeklyResult`; canonical complaint counts, trends, attribution and policy gaps. |
| HTTP-06 | `GET /api/health` | None | Proposed health/readiness result; safe dependency and feature availability, without paid model probes. |

### HTTP-01 — submit a complaint

`email_text` is a nonblank string. Omitted/null `session_id` creates a conversation; an existing ID refers to that complaint context and must not silently overwrite another session. Normal follow-ups use HTTP-02; a supplied unknown session returns `404 SESSION_NOT_FOUND`.

```json
{"email_text":"Please investigate delivery for order 99999.","session_id":null}
```

Run deterministic input checks, resolve order candidates and request clarification when evidence cannot distinguish v1/v2. Retrieve facts at question time, compute rules in code, mask model context, validate the answer and save the resulting workflow state. Do not count a pasted email as a new canonical case or assume the customer's claim is verified.

### HTTP-02 — follow up or clarify

At least one of `message` or `selected_candidate` is required. If both are supplied, the candidate selects context and the message is evaluated within it; conflicting instructions require clarification. The server validates candidate eligibility against the session and source dates rather than trusting the browser.

```json
{"selected_candidate":{"system_version":"v1","order_id":99999}}
```

```json
{"message":"What evidence supports that recommendation?"}
```

Keep the session ID, append the turn, preserve evidence/conflicts and re-run only the tools needed for the question. Follow-ups do not create additional complaints. Missing policy, missing evidence and out-of-scope requests remain explicit outcomes.

### HTTP-03 — recover a session

Return the last saved result, workflow state and sanitised message history; preserve candidate choices, citations and limitations. `messages` contains `{role: "user" | "assistant", text: string}` records, with optional timestamps. Recovery itself does not repeat model calls or ingestion. Unknown sessions return `404 SESSION_NOT_FOUND`.

The browser remembers only the last session ID in `localStorage`. Backend state must survive a process restart in the proposed SQLite store; the mock's `sessionStorage` is not evidence of server persistence. Keep sessions isolated; a source-version change must not silently relabel old evidence as current.

### HTTP-04 / HTTP-05 — weekly reporting

The current UI chooses the last entry from HTTP-04 and then calls HTTP-05. Return `weeks: []` when the published dataset has no available weeks; the UI must show no data without requesting `week_start=null`.

```json
{"weeks":["2026-05-18","2026-05-25"],"timezone":"Asia/Singapore","synthetic":false}
```

The proposed week is Monday–Sunday SGT by complaint Date Opened, subject to final reporting agreement. Derive totals from published canonical cases and the driver/zone views, retaining unknown attribution and duplicate exclusions; do not substitute email counts. A valid covered week with zero complaints returns zero complaint counts; a week outside published coverage returns `404 NO_DATA`. Unavailable calculations return explicit limitations and nullable metrics, not invented zeros.

### HTTP-06 — health/readiness

Proposed fields: `request_id`, `status` (`ok`, `degraded`, `failed`), safe dependency states and per-feature availability for `triage`, `weekly`, `sessions` and semantic retrieval. A disabled optional semantic index is distinct from a failed dependency. Use `200` for healthy/degraded service with usable features and `503` when the application cannot serve its core features; never expose credentials, raw database exceptions or client records.

Feature readiness may come from this endpoint or explicit frontend configuration; neither mechanism is implemented yet. Health checks must not pay for image extraction, embeddings or answer generation.

## 3. Shared response contracts

### 3.1 ComplaintResult

Keep fields stable for the existing renderer: absent objects are `null`, collections are `[]`. Unless noted otherwise, the fields below apply to complaint and follow-up results; recovery adds saved messages.

| Field | Shape / meaning |
|---|---|
| `request_id`, `session_id`, `status` | Trace ID, conversation ID and domain outcome. Session ID may be null if processing is refused/fails before allocation. |
| `complaint` | `{category, claims: string[], citations: integer[]}`; claims remain attributed statements. |
| `order` | Nullable `{system_version, order_id, customer, postal_code, zone, driver_code, promised_date, citations}`; personal fields masked. |
| `candidates` | `{system_version, order_id, created, status, zone, postal_code, evidence_for, citations}[]`; preserve supporting/excluding evidence. |
| `clarification` | Nullable `{question, hint}`; no arbitrary candidate selection. |
| `evidence` | `{key, title, status, summary, facts: [string, string][], citations}[]`; keys include `delivery`, `pod`, `gps`, `rate`, `policy`. |
| GPS evidence fields | Optional `gps: {t: string, dist: number}[]`, `deliveredAt`, `note`; proposed `dist` is metres and display times are SGT. Keep raw epoch, normalisation and source lines in tool provenance. Confirm distance derivation before plotting. |
| `conflicts` | `{field, values: {value, source, citation}[], note}[]`; show both cited observations, without silently picking one. |
| `recommendation` | Nullable `{action, amount_sgd, summary, rationale, approval_required, approver, citations}`. Action: `Refund`, `Re-deliver`, `Reject`, `Apology only`, `Compensate`. Escalation is descriptive; no execution endpoint. |
| `abstention`, `guardrail` | Nullable `{reason}` and `{code, pii_masked: string[]}`; distinguish insufficient evidence from deterministic refusal. |
| `follow_up_answer`, `limitations` | Nullable answer text and `string[]` limitations. |
| `citations` | Numbered source records defined below; every referenced number must exist. |
| `error` | Nullable `{code, message, retryable}`. Required non-null for a body-level `failed` outcome; this field extends the original UI draft. |
| `recovered`, `messages` | Recovery flag; `messages` is added on session recovery. |

`recommendation` is null for ambiguous, refused, not-found or failed cases, and whenever policy/evidence cannot support an action. A `partial` result may recommend only what the available evidence safely supports. Never turn an unverified claim, calculated charge or uncertain signature into an established fact.

### 3.2 Status and error handling

HTTP status describes request handling; body `status` describes the complaint outcome. The HTTP error mapping below is a **proposed extension** to the draft consumer contract.

| Domain status | Meaning / UI treatment |
|---|---|
| `found` | Sufficient cited evidence for the displayed result. |
| `ambiguous` | Multiple eligible identities/interpretations; show candidates and clarification. |
| `partial` | Useful evidence with a source failure, uncertainty or conflict; disclose limitations. |
| `not_found` | Search completed but relevant evidence/identity is unavailable; abstain honestly. |
| `refused` | Deterministic policy/input refusal; avoid unnecessary model calls. |
| `failed` | Dependency/processing failure; enter the error flow and respect `error.retryable`. |

| HTTP status | Use / example code |
|---|---|
| `200` | Completed domain result, including ambiguity, missing evidence and refusals. A `failed` body is also allowed by the existing draft but must not be treated as normal success. |
| `422` | Invalid request fields, blank input or malformed date/identity: `VALIDATION_ERROR`. |
| `404` | Missing session or reporting coverage: `SESSION_NOT_FOUND`, `NO_DATA`. |
| `503` | Required dependency unavailable: `DEPENDENCY_UNAVAILABLE`. |
| `504` | Server-side dependency deadline exceeded: `DEPENDENCY_TIMEOUT`. |
| `500` | Unexpected server failure: `INTERNAL_ERROR`; safe message, no raw exception. |

```json
{"request_id":"req-example-001","error":{"code":"DEPENDENCY_UNAVAILABLE","message":"Delivery records could not be checked. Please retry.","retryable":true}}
```

The current client aborts after 45 seconds and creates local `TIMEOUT` or `NETWORK` errors without an HTTP response. Align server/tool budgets with that deadline; the existing offline vision client's longer timeout is not the live-request budget. Bound retries and retry only eligible failures; final limits, input-size limits and POST retry deduplication/idempotency remain implementation decisions. A browser timeout does not prove the server stopped or that a repeated model call is free.

### 3.3 Citation

Public shape: `{n, source_id, type, ref, locator, record_key, label?}`. `n` is the per-response display number; `type` is `sql`, `tabular`, `image`, `document` or `log`. `record_key` is nullable and source-specific: unresolved email keys can contain `order_numbers`, while resolved order keys use `system_version`/`order_id`.

| Source | Locator / verification rule |
|---|---|
| SQL | Table plus composite order/delivery/driver key; preserve query/batch provenance. |
| Email | `body:char:<start>-<end>` into the original parsed body; check the original span before masking the display text. |
| Guide | `sheet:Resolution Guide\|row:<n>`; preserve guide version and client authority. Use full rule fields, not only truncated search snippets. |
| POD | Original image plus `field:<name>`; retain raw observation, confidence, extraction version and SQL comparisons. |
| Rate | Original card plus `row:<zone>/col:<band>` and applicability authority. |
| GPS / case workbook | Original file plus line or sheet/row; retain raw/normalised timestamp and transformation references. |

The existing citation renderer assumes every non-null record key is an order pair; extend it to display source-specific keys without printing undefined values. Current UI citation links point to the on-page source list, not a file-download endpoint. Source-root mapping must resolve logical refs to actual local evidence for verification. An inline original-image/download API is an open extension; do not treat `ref` as a browser URL or expose arbitrary filesystem paths.

### 3.4 WeeklyResult

| Field | Required content |
|---|---|
| `period` | `{week_start, week_end, timezone}`. |
| `definitions` | `[label, explanation][]`: week, canonical complaint, deduplication, zone derivation, unknown attribution and guide-gap interpretation. |
| `totals` | `rows_logged`, `complaints`, `duplicates_merged`, `compliments_excluded`, `unknown_zone`, `unknown_driver`, `refunds_sgd`, `vouchers_sgd`, `approvals_needed`, `approvals_missing`, `guide_gaps`. Unavailable financial/policy metrics are nullable. |
| `by_zone`, `by_driver` | `{zone, complaints}[]`; `{driver_code, complaints, main_zone, top_category}[]`; use stable identities and keep unknown attribution visible. |
| `by_category`, `by_resolution` | `{category, complaints}[]`; `{resolution, cases}[]`. |
| `zone_category` | `{zones, categories, rows: {zone, values: number[]}[]}` with aligned axes. |
| `trend` | `{week_start, total, by_zone}[]`; UI draft requests a 12-week trend, limited to known coverage and with limitations stated. |
| `limitations`, `citations` | Missing-input/calculation notes and verifiable case/SQL/rule lineage. |

Operations zones are North, North-East, East, Central and West, plus Unknown for unresolved attribution. Pricing zones are separate. Compare historical agent resolutions with guide v2; do not change historical actions. Unknown approvals/gaps must remain distinguishable from confirmed compliant/noncompliant outcomes. Nullable metrics, empty lists and insufficient-evidence states need frontend handling before live integration; the current fixtures assume complete numeric metrics.

## 4. Internal Python tool catalog

These run inside the backend. Existing callable signatures come from source; newly named services below are proposed interfaces rather than implemented functions.

### 4.1 Existing unstructured tools

| ID | Callable | Input / output and limits |
|---|---|---|
| TOOL-01 | `search.search_emails(query="", order_number=None, *, top_k=5, out_dir=...)` | Keyword/synonym ranking over `emails.jsonl`; optional exact order-number filter. Hits: `text`, `score`, `category`, `is_complaint`, `received_at`, `order_numbers`, citation. Returns original, unmasked snippets. |
| TOOL-02 | `search.search_policy(query="", effective_date=None, *, category=None, top_k=5, out_dir=...)` | `policy_chunks.jsonl` guide hits: `text`, `score`, `heading`, `fields`, `guide_version`, `authority`, citation. Category maps to the rule; the client applies guide v2 to every case, so date is not a historical-version filter. |
| TOOL-03 | `pod.find_pod(records, source_system, order_id)` | Caller loads published `pod_records.jsonl`; exact system/order lookup returns extracted fields, confidence, flags, source and SQL validation. Never reuse a v1 scan for a v2 order. |
| TOOL-04 | `ratecard.lookup_rate(cards, *, zone, weight_kg, on_date)` | Caller loads `rate_cards.jsonl`; returns base standard price, band, currency, pre-GST flag, mapped price zone, retrospective flag, notes and cell citation. It is not the complete charge/refund calculation. |

Modules are under [`backend/unstructured/`](../../backend/unstructured/README.md). Tools read cached evidence at request time and do not call vision models. Search currently uses lexical/category ranking, not embeddings; `out_dir`/loaded records must refer to the published batch.

Existing envelope:

```json
{"ok":true,"status":"not_found","data":[],"sources":[],"error":null}
```

`data` can be an object, list or null depending on the tool; optional `reason` explains an empty outcome. `sources` contains source IDs, while citations live in returned records. Search uses `ok=false` for `failed`; POD/rate helpers currently return `ok=true` even for partial/absent results. Adapters must inspect `status`, extraction outcomes and exceptions rather than treating `ok` as proof of usable evidence.

Search errors include `INDEX_MISSING`, `SOURCE_MISSING`, `EMPTY_SOURCE` or a parser/format error surfaced by the manifest. Missing files, failed extraction, no matching record and no policy rule are different states. In particular, a compliment with no policy rule returns `not_found`; a missing guide/index returns `failed`.

### 4.2 Proposed structured and RAG services

Names/arguments in this table are proposed; their implementation can change behind the six HTTP contracts. Return cited records or the shared tool envelope, with `ambiguous` supported for unresolved identities/rates.

| ID | Service / proposed inputs | Result / responsibility |
|---|---|---|
| TOOL-05 | `resolve_order(order_number, received_at, system_hint=None, contact_context=None)` | Candidate list or verified composite identity; exclude orders created after the complaint and preserve reasons. Contact/case-log links are evidence, not automatic matches. |
| TOOL-06 | `get_delivery_history(system_version, order_id)` | Latest exported attempt with delivery/driver citations; retain the established service name but explicitly state that earlier attempts/counts are unavailable. |
| TOOL-07 | `get_gps_window(driver_id, start_utc, end_utc)` | Cited driver/time pings with raw epoch, normalised time and alignment assumptions; distance requires a supported location reference. |
| TOOL-08 | `get_pod(system_version, order_id)` | File-loading/identity adapter over TOOL-03; preserve extraction failure, identity conflicts and source locators. |
| TOOL-09 | `get_rate(system_version, order_id, on_date)` | TOOL-04 plus reviewed town/price mapping, standard service, CBD timing, calendar checks, GST and applicable COD fees. Return a calculation breakdown and missing inputs; calculated charges are not verified amounts paid. |
| TOOL-10 | `weekly_complaints(week_start)` | `WeeklyResult` from published canonical cases, member lineage and weekly SQL views. Prepare source-backed guide-gap metrics only where facts permit. |
| TOOL-11 | `retrieve_evidence(query, category, resolved_order=None)` | Merge exact/category/keyword hits with optional semantic top-k, filtered by source/batch and verified identity. Embeddings use the same model/dimension at index and query time. |
| TOOL-12 | `assess_resolution(case_context, evidence, policy)` | Deterministic policy/charge checks, missing evidence, approval requirement and corporate-month counts; no universal source hierarchy. |
| TOOL-13 | `answer_complaint(session_state, evidence, assessment)` | Masked context → answer model → claim/citation/PII checks; emit `ComplaintResult` with limitations or abstention. |
| TOOL-14 | Session load/save interface | Persist messages, selected candidates, workflow, evidence/version references, conflicts, recommendations, citations, usage and safe errors; isolate sessions and restore without recomputation. |

All source joins and arithmetic are Python/SQL operations. Missing GPS alignment, approval records, declared value, proof of purchase, photos or prior attempts stay unknown; the model must not fill these gaps.

## 5. Offline preparation and provider interfaces

| Interface | Status / input → output |
|---|---|
| Database bootstrap / seeding | Manual [SQL import](../../database/createdb_seed_sql_data.md) exists. Proposed bootstrap applies versioned DDL for the three case tables and two views; no runtime reset. |
| Case ingest / transform | Proposed: preserve 505 workbook rows in `raw_case_log`, then canonicalise into `clean_cases` and `clean_case_members`. Same-batch replay is idempotent; retain business-duplicate evidence and rule history. |
| GPS/reference preparation | Proposed: retain original JSONL, validate epoch/alignment, build file-backed access and reviewed operations/pricing mappings; source/version the SG holiday calendar. |
| `python -m backend.unstructured.ingest --data <root> --out <dir>` | Existing: emails and guide → `emails.jsonl`, `policy_chunks.jsonl`, `manifest.json`; no model calls. Guide discovery expects the selected package's `tabular/` or `docs/`, not an arbitrary workbook elsewhere under `data/`. |
| `python -m backend.unstructured.extract_images --data <root> --out <dir> --sql <dump>` | Existing: images → `pod_records.jsonl`, `rate_cards.jsonl`, `image_manifest.json`, cache/telemetry/spend records. `--dry-run` is free; `--limit N` limits POD images, while the rate card is still included unless `--only pod` is set. |
| Semantic index build | Proposed: source-bounded email/guide chunks, original locators and masked text → versioned vectors + citation metadata. Cache by source/chunk/masking/chunker/model version; compare against lexical relevance before enabling. No indiscriminate embedding of SQL identities/numbers. |
| Batch publication | Proposed: validate/reconcile SQL, evidence, references and index versions; publish one restart-safe manifest. Later SQL dumps use staging; new batches never silently extend current retrospective rate authority. |
| Class model provider | Existing vision client posts to configured `OPENAI_BASE_URL` + `/chat/completions` using server-side `OPENAI_API_KEY` and configurable `A_VISION_MODEL`. Answer and embedding clients/capabilities remain proposed; no public model-proxy endpoint. |

Image extraction caches by image hash + prompt version + model; unchanged inputs reuse results, and deliberate changed/failed-input reprocessing retains outcomes. Keep a record/manifest entry for every failed input. Vision extraction preserves printed values; code performs normalisation and comparison, without silently overwriting conflicts. No SQL evidence migration is required for the demo.

## 6. Client rules and integration constraints

| Area | Required behaviour |
|---|---|
| Counting / policy | One complaint per case; follow-ups remain in that case; report duplicate incidence. Guide v2 applies across dates and is the authority for comparing historical agent actions. |
| Zones / time | Five address-town operations zones are separate from pricing bands, including special-area prices. GPS is Unix seconds and operations timestamps are SGT; investigate residual offsets against the approximate 07:00–23:00 driver window. |
| POD / latest attempt | Look for a matching system/order record in the published evidence. When absent, say **“No POD on file for this order in the supplied dataset.”** Do not imply a scan was checked, substitute another system's image or impose a hard date that rejects a later supplied POD. Earlier attempts are unavailable. |
| Image uncertainty | Filename identity, image identity and approved order link remain separate where they conflict. Preserve COD card/SQL values and their citations. A signature is not recipient identity; an “absent” signature needs the flagged by-eye verification. |
| Rate / charge | April card applies retrospectively to supplied orders with client Q06 authority; upper bounds 3/10/25 kg are inclusive. Nonpositive weight is invalid; over 25 kg needs a manual quote. All exported orders are standard. Derive CBD/07:30–19:00 and public-holiday checks; do not invent prior-attempt counts/fees. |
| Resolution / escalation | Check COD against recorded amounts and handling rules; never refund the claimed amount without checking. Guide amounts/required evidence govern recommendations; refunds over S$50 and corporate 3+ complaints per month require Head of CX involvement. No operational action is executed. |
| Identity / personal data | No NRIC-based verification. Keep credentials server-side, remove prohibited identifiers from new session/log records and mask personal fields before answer/embedding/browser exposure. |
| Traces / spend | Link request/session/tool events with status, latency, model, prompt/index versions, token use, cache state, bounded attempts and safe errors. No raw prompts, queries, images or answers in telemetry. Track cumulative spend without counting cached extraction twice; unknown costs remain unknown. |

### Known implementation gaps from handoff review

1. **Policy category + query:** current keyword filtering can discard a valid category rule. Until fixed, use the exact category path without an unrelated query; the target retains category matches independently of lexical overlap.
2. **Rate expiry:** current retrospective fallback can reuse an explicitly expired card after its end date. The target respects end dates and limits back-dating to authorised earlier dates/source scope.
3. **POD status/message:** remove the fixed migration-date explanation, permit later matching records and propagate actual extraction failures rather than flattening them into partial evidence.
4. **Masking/paths:** free-text names need additional coverage; logical refs need configured root resolution. Public citations need source-specific key rendering; original image verification uses local source access until an evidence-viewer contract exists.
5. **Persistence/API:** current browser mocks are not backend recovery. SQL tools, shared request telemetry, session persistence, answer orchestration and optional embeddings remain unimplemented.

## 7. Frontend integration and acceptance

| API state | Demo profile | Live profile |
|---|---|---|
| Feature endpoint unconfigured | Synthetic fixture with prominent **Demo Data** label. | Block that call; show **Not connected**. |
| Configured API succeeds | Real response; label source accurately. | Real response; optional **Live** label. |
| Configured API fails | Error state; no fixture fallback. | Error state; no fixture fallback. |
| API succeeds with no records | **No data found**; no fixture fallback. | **No data found**; no fixture fallback. |

Apply this per feature, preserve usable features when another fails, and clear or visibly distinguish stale results. An empty base URL can mean same-origin `/api` calls, not an unconfigured endpoint. The current global mock switch/base check does not implement this handoff. Add `dev:demo`, `dev:live`, `build:demo`, `build:live` using Vite `--mode demo` / `--mode live`, with `VITE_USE_MOCK=true` in `.env.demo` and `false` in `.env.live`; parse strings explicitly, document configuration and restart/rebuild after changes. These profiles remain frontend work. Demo permits fixtures for unconfigured features; it does not force fixtures when a real endpoint is configured.

- HTTP 200 + `status: failed` enters the error flow, preserving `error.retryable`; offer Retry only when allowed. A weeks-list failure retries that initial list→selected-week sequence, while a selected-week failure retries its valid date.
- Preserve the triage form, ambiguity, conflicts, approval flag, refusal, unavailable-source, follow-up and recovery journeys. Weekly fields support the existing KPI tiles, zone trends, driver rankings, zone/category matrix, resolution mix, filters and accessible table equivalents. The explainer screen is static; no extra endpoint is required.
- Verify mixed feature availability, source labels, same-origin calls, nullable metrics, source-specific citation keys, empty lists, HTTP/body failures and both retry paths. Run lint and both demo/live builds when those profiles land; handoff screenshots/mock checks do not establish live integration.
- Release checks cover at least 20 eval questions, at least two refusals and five kill-shot phrasings; preserve and consolidate existing component/journey cases. Test fresh setup, identical/overlapping/new batches, malformed data, interrupted publication, source/rate boundaries, citation support, a killed dependency and real backend restart recovery. Record PASS/FAIL/PENDING explicitly; reported historical 12/18-case runs are not a new integrated pass.

## 8. Contract decisions still to confirm

| Decision | Proposed position / remaining agreement |
|---|---|
| HTTP contract freeze | Adopt the six existing client paths and display-ready result fields; confirm validation limits, transport mappings and framework choice before implementation. |
| Reporting definitions | Agree Mon–Sun/Date Opened rules, canonical-case matching, coverage, guide-gap/approval definitions and nullable metric handling. |
| Session/retry semantics | Agree retention, isolation/access checks, existing-session submit behaviour, concurrent turns, source-version changes and POST deduplication after a timeout. |
| Readiness / source selection | Agree per-feature configuration and optional health capability fields; implement the reviewed demo/live matrix. |
| Evidence viewing | Confirm whether on-page locators plus local source verification suffice for the demo, or define a controlled original-evidence viewer. |
| Semantic retrieval | Confirm permitted embedding capability/model, versions, relevance benefit, failure policy and publish/rebuild procedure; lexical retrieval remains available. |

## 9. Sources and handoff review

Read with the [overall architecture](architecture_overall.md), [release draw.io design](merlion-express-technical-architecture_v1.drawio.svg), [frontend contract draft](frontend-ui-contract-draft.md), [technical contracts](contracts_2026-11-16.md), [database design](database-design_2026-11-16.md) and [hosting scope](hosting-options.md). Current function signatures were cross-checked against the frontend client and unstructured backend source.

The 17 Nov guide/client-answer handoff supersedes the 16 Nov missing-guide, ambiguous 3/10 kg and unavailable pre-April-rate descriptions. The current release design supersedes the early instruction to move all POD/rate evidence into SQL; the API/mock handoff supersedes the global fixture-selection behaviour. Review findings remain fixes to implement, not claims that they have landed.

A separate [handoff coverage review](../05-Reviews/api-catalog-review_2026-11-17.md) records the single review pass against every document in `03-Handoffs`, including non-contract items and unresolved work.
