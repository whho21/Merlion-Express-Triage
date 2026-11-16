# Database design and reconciliation with Developer A

**Updated:** 16 Nov 2026, SGT. **Status:** Proposed design; no database migrations or loader changes have been executed by this review.

## 1. Design decision

Use MySQL for structured facts, cleaned complaints, joins, calculations and evidence metadata. Keep original files and extraction caches under ignored `data/` and `output/`. Reuse Ralph's existing extraction records, provenance and retrieval tools rather than implementing a second extraction pipeline.

**Use one database: `merlion_express`, with separate raw and cleaned tables.** Keep the instructor’s `orders`, `drivers` and `deliveries` names unchanged. Prefix every new table by purpose: `raw_` for staged source rows, `clean_` for validated application data, and `meta_` for provenance/run metadata. Use `view_` for Gold/reporting views, not `vw_`. Database location does not define the data layer; raw, cleaned, metadata and reporting objects coexist in this database. Do not clean the instructor tables in place or restore a dump over application tables.

Raw preservation does not require a duplicate database table for every file. Keep the original workbook, JSONL, email and image files immutable. Use a raw case table because spreadsheet rows need explicit typing, cleaning and deduplication lineage. Use typed GPS rows with the original epoch and source line, retaining the original JSONL as raw evidence.

### ELT instruction — preserve first, transform before serving

Follow **Extract → Load → Transform (ELT)** for source-data preparation:

1. **Extract/load raw:** preserve all supplied records, including duplicate complaints, inconsistent values and original source locations. Do not deduplicate or silently repair business data during raw ingestion. Invalid records remain in raw storage or a traceable reject record if they cannot be represented safely. Prevent replay of the identical batch from creating extra raw copies; this technical idempotency is distinct from business deduplication.
2. **Transform separately:** run parameterised, versioned pipeline steps to normalise types/categories/zones, resolve identities, identify duplicate complaints and populate `clean_` tables. Transformations may use SQL or Python/pandas; ELT does not require every transformation to be SQL. Preserve original values, source links, rule versions, uncertain matches and rejected outcomes.
3. **Validate/publish:** reconcile raw, cleaned, duplicate and rejected counts before making the transformed batch available to application queries. Reprocessing under a revised rule is an explicit run, not a silent change during a request.
4. **Serve through API/tools:** query published cleaned tables and reporting views. Do not re-import files, clean dates, infer zone spellings or deduplicate the source dataset inside each API request. Keep pipeline modules separate from request handlers, even when they share one Python application.

For the current case workbook, load all **505 source rows** into `raw_case_log`; derive canonical complaints in `clean_cases`; retain every original-row association and deduplication reason in `clean_case_members`. The resulting complaint count is determined by reviewed rules, not assumed to equal 505. Raw records remain available for audit and reprocessing.

Question-specific work remains at request time: reporting-period filters/aggregations, candidate clarification, GPS-window selection, evidence retrieval, applicable rate calculations and policy checks against the requested case. These operations use validated data and versioned rules; they are not substitutes for the preparation pipeline.

The table owner owns the raw-load and transformation components applicable to their tables. C orchestrates the batch and publication boundary; E verifies fresh load, identical-batch rerun, revised-rule transformation and a subsequent client batch. API requests must not trigger a full transformation or paid re-extraction.

## 2. Sources and confirmed authority

| Source | Current evidence / design consequence |
|---|---|
| `data/team2_merlion_express_package/sql/merlion_ops.sql` | Raw drivers, orders and latest delivery records; order numbers repeat across systems |
| `data/CS_case_log_Oct25-Jun26.xlsx`, Case Log | 505 rows; preserve all rows, then identify duplicate complaints without deleting evidence |
| Same workbook, Resolution Guide | Nine complaint-type rules plus general notes; retain worksheet row/cell citations |
| [Client Q&A v02](../00-Biz_Requirements/client_qa_v02.xlsx), Q01–Q08 | Client authority supplements the source files; answers and printed source content remain distinguishable |
| Original POD/rate-card images | File identity is not equivalent to image content; preserve images for citations |
| Ralph's `output/unstructured/` records/manifests | Existing extraction handoff to load, not a replacement for original evidence |

Client-confirmed rules to encode and test:

- One complaint equals one case; follow-ups belong to that case. Duplicate case-log entries should count once, with the duplicate count reported. Unique Case No values do not prove complaints are distinct.
- The current guide applies to all cases, including those before its printed version date. Compare historical agent actions against the guide; do not treat historic actions as policy authority.
- Reporting uses five operations zones. Pricing groups them differently and treats Sentosa/Jurong Island separately. Determine town from delivery address; do not assume the two zone concepts are interchangeable.
- Only the latest delivery attempt is available. Earlier attempt counts cannot be reconstructed from this export. No additional v2 POD export is available.
- Delivery timestamps are Singapore local time. GPS values are Unix seconds; empirical alignment/clock-offset investigation is still required. Never apply an unexplained eight-hour adjustment.
- Apply the April rate card retrospectively to the supplied orders, citing Q06. Upper weight limits are inclusive: `0 < w <= 3`, `3 < w <= 10`, `10 < w <= 25`; invalid/nonpositive and over-25 weights require explicit handling.
- Exported orders are standard delivery. CBD timing and public holidays need derived inputs; third-attempt charges must be referred for confirmation when attempt count is unavailable.

## 3. Complete proposed data-table inventory

The baseline is three preserved source tables plus seventeen proposed application tables. These are small relational responsibilities, delivered in stages, not seventeen independent services. Optional runtime/retrieval tables are identified separately in Section 9.

### Bronze — preserved instructor tables in `merlion_express`

| Table | Purpose | Identity / treatment | Create + load owner | Current code status |
|---|---|---|---|---|
| `drivers` | Unmodified driver export | Existing `driver_id`; do not merge drivers by name | B / Jenn Fang | Instructor dump contains DDL and data; manual seeding commands exist. Automated periodic-batch importer not implemented. |
| `orders` | Unmodified order export | Raw instructor table lacks a declared primary key; `(system_version, order_id)` is unique in the supplied dump | B / Jenn Fang | Instructor dump contains DDL and data; manual seeding commands exist. Automated periodic-batch importer not implemented. |
| `deliveries` | Unmodified latest-attempt export | Existing `delivery_id`; not a complete delivery-event history | B / Jenn Fang | Instructor dump contains DDL and data; manual seeding commands exist. Automated periodic-batch importer not implemented. |


### New prefixed tables in `merlion_express`

| Table | Purpose | Primary identity and main relationships | Create + load owner | Current code status |
|---|---|---|---|---|
| `meta_source_documents` | Register originals and source versions: relative path, hash, type and logical source ID | `document_id`; unique `(relative_path, sha256)`; preserve Ralph's source ID as an external identifier | C / John | No MySQL DDL/loader. A’s file hashes/manifests are reusable inputs. |
| `meta_ingestion_runs` | Record loader/parser/model/prompt versions, start/end, outcomes, counts and configuration hash | `run_id`; common `batch_id`, optional `parent_run_id`, component, stage/publication status and source manifest; referenced by loaded/extracted records; no credentials in configuration | C / John | No MySQL DDL/loader. A’s manifests/telemetry exist as files. |
| `raw_case_log` | Lossless staged case-log rows before cleaning, including source values/types and parse issues | `raw_case_id`; unique `(document_id, sheet_name, row_number)`; source and ingestion references | B / Jenn Fang | No MySQL DDL/loader; received XLSX must be parsed. |
| `clean_drivers` | Validated driver IDs/codes used by case attribution and GPS joins | `driver_id`; validated unique `driver_code`; source reference | B / Jenn Fang | No cleaned-table DDL/loader; raw source exists. |
| `clean_orders` | Cleaned orders with original identity, validated dates/postal strings and standard-service provenance | Composite PK `(system_version, order_id)`; source reference; zone assignments reference reviewed mapping | B / Jenn Fang | No cleaned-table DDL/loader; raw source exists. |
| `clean_deliveries_latest` | Cleaned most recent recorded attempt per order, preserving raw local time and derived UTC | `delivery_id`; unique `(system_version, order_id)` for this export; FK to orders and driver | B / Jenn Fang | No cleaned-table DDL/loader; raw source exists. |
| `clean_cases` | One canonical complaint, cleaned fields, historical action/refund/voucher, resolved order/driver/zone and resolution status | `case_id`; nullable composite order FK; nullable driver FK; unresolved identity remains explicit | B / Jenn Fang | No MySQL DDL/loader or canonical-case pipeline. |
| `clean_case_members` | Map every original case-log row to its canonical complaint, with deduplication rule/version/reason | `raw_case_id` as PK/FK, `case_id` FK; multiple source rows may map to one case; no silent deletion | B / Jenn Fang | No MySQL DDL/loader or persisted deduplication lineage. |
| `clean_gps_pings` | Queryable driver/time/location observations with raw epoch, normalised UTC and alignment provenance | `ping_id`; driver FK; `(document_id, line_number)` unique; index `(driver_id, ts_utc)` | B / Jenn Fang | No MySQL DDL/loader; JSONL source exists. |
| `clean_pod_evidence` | Versioned image extraction and filename identity, field confidence, SQL comparisons and conflicts | `pod_id`; document/run FKs; unique `(document_id, extraction_version)`; nullable validated order FK | A / Ralph | Image extraction/JSONL exists; MySQL DDL/loader not implemented. |
| `clean_policy_rules` | Source guide rows and general notes, conditions, limits and required approval roles | `policy_rule_id`; document/worksheet row locator, guide version and authority references; code enforces reviewed rules | A / Ralph | MD/TXT/CSV parsing exists; Excel guide support and MySQL DDL/loader not implemented. |
| `clean_rate_cards` | Source card, currency, printed effective date, extracted notes and client-approved applicability | `rate_card_id`; source/run FKs; authority document and Q06 locator for retrospective use | A / Ralph | Image extraction/JSONL exists; MySQL DDL/loader and clarified applicability changes pending. |
| `clean_rate_prices` | Structured standard price per pricing zone and non-overlapping weight interval | `rate_price_id`; card FK; unique `(rate_card_id, pricing_zone, min_kg, max_kg)`; explicit inclusive/exclusive bounds | A / Ralph | Extracted price rows exist; MySQL DDL/loader and confirmed boundary handling pending. |
| `clean_rate_surcharges` | Card surcharge/fee formulas, applicability, availability and required inputs | `surcharge_id`; card FK; source locator; typed amount/percent/minimum where applicable plus original rule text | A / Ralph | Extracted surcharge records/notes exist; MySQL DDL/loader not implemented. |
| `clean_zone_mapping` | Reviewed town mapping to operations zone, pricing zone, special-area treatment and CBD district classification where known | `mapping_id`; reviewed normalised town/match rule; authority, mapping version and review status; unknowns remain explicit | B / Jenn Fang | No MySQL DDL/loader or approved mapping seed implemented. |
| `clean_calendar_dates` | Relevant Singapore dates, public-holiday flags and documented working-day treatment | Date PK; calendar source/version; do not invent Saturday/working-day rules where unspecified | E / Ho Wai Hong | No MySQL DDL/loader or sourced calendar seed implemented; B/C review rules. |
| `clean_complaint_emails` | Ralph's parsed email records, original body/claims/locators and optional verified case association | `email_id`; document FK; unique source document; nullable case FK; retain multiple order-number candidates in JSON | A / Ralph | Email parser/search/JSONL exists; MySQL DDL/loader not implemented. |


There is no additional compulsory `rates` or `raw_pod` table: `clean_rate_cards`/`clean_rate_prices`/`clean_rate_surcharges` and the original images plus `clean_pod_evidence` cover those responsibilities. The earlier suggested `rate_rules` and `public_holidays` names are replaced by this explicit inventory.

### Naming and layer rules

| Layer / purpose | Prefix | Examples | Meaning |
|---|---|---|---|
| Bronze | `raw_` | `raw_case_log` | Source-preserving staging rows; instructor tables are the only naming exceptions |
| Silver | `clean_` | `clean_orders`, `clean_cases`, `clean_pod_evidence` | Validated facts, evidence, mappings and rules; a clean evidence row can still carry uncertainty/conflicts |
| Gold | `view_` | `view_weekly_complaints_by_driver` | Business queries over reviewed data; views do not store separate copies of results |
| Shared metadata | `meta_` | `meta_source_documents`, `meta_ingestion_runs` | Source/run lineage and publication control; not a Silver business layer |

All PK/FK references and loader queries must use the prefixed target names. For example, `clean_deliveries_latest` references `clean_orders` and `clean_drivers`; `clean_case_members` links `raw_case_log` to `clean_cases`; extraction tables reference `meta_source_documents` and `meta_ingestion_runs`. Preserve Ralph's filenames (`rate_cards.jsonl`, `pod_records.jsonl`, `emails.jsonl`), Python module/tool names and field contracts: table prefixes are applied by the SQL adapters only.

### Proposed Gold views (additional to the twenty physical tables)

| View | Purpose | Create owner | Current code status |
|---|---|---|---|
| `view_weekly_complaints_by_driver` | Deduplicated weekly complaints by stable driver ID, including unknown attribution | B / Jenn Fang | Not implemented; owner supplies CREATE VIEW migration and check queries |
| `view_weekly_complaints_by_zone` | Deduplicated weekly complaints across the five operations zones, including unknown attribution | B / Jenn Fang | Not implemented; owner supplies CREATE VIEW migration and check queries |

Views consume published/validated data under the agreed week/timezone rules. They have no independent data loader: B owns the view definition and verifies its output after source table loading. Dynamic question-specific calculations and policy decisions can remain service queries; do not force all logic into views.

## 4. Raw versus cleaned field rules

- Preserve the original Excel file and every source row. `raw_case_log.raw_values` is JSON that records each cell's value/type; preserve date text without guessing day/month order. The workbook is the final source for original cell representation.
- Store normalised dates and financial amounts separately. Use `DECIMAL`, not floating-point, for money. A blank refund is not automatically zero; capture missing/parse-failed/zero distinctly.
- Case-log Date Opened/Closed contain mixed Excel dates and strings; some typed dates extend into July despite the filename. Validate interpretation and reporting scope instead of truncating to June.
- Normalise category/zone spelling through reviewed mappings. Keep the original case-log zone/driver even when deriving an alternative from the resolved order; expose discrepancies.
- Resolve order references using system-aware order candidates and supporting identity/date evidence. Unresolved cases remain in reporting unknowns; do not force them onto an arbitrary v1/v2 order.
- Deduplication must not merge separate complaints merely because they share an order. Preserve the evidence and rule version in `clean_case_members`; uncertain groups need review rather than silent collapse.
- Record source identifiers, row/line/field locators, transformations and applicable client authority. Do not overwrite a conflicting POD value with SQL or a historical action with the policy recommendation.
- Separate document versions and ingestion versions from current business records. Reloading the same source/version must not create duplicate cases, pings or evidence.

## 5. What a POD filename does and does not establish

For `POD_v1_23931.jpg`, filename parsing supplies only the claimed `v1` system and `23931` order identity, together with the file reference/hash. It does not establish delivery date, driver, recipient, location, condition, signature or COD collection.

Ralph has already implemented image-content extraction in [pod.py](../../backend/unstructured/pod.py) and the runner [extract_images.py](../../backend/unstructured/extract_images.py). The vision prompt reads order reference, date/time, driver, delivered-to address, receiver, remarks, signature presence and other card text; Python normalises and compares selected fields with SQL. This is more than filename parsing. His [handoff](../03-Handoffs/Ralph_2026-11-16-A-tools-evidence-limits.md) reports an 80-image run; this design review did not rerun paid extraction or independently certify those outcomes.

Recommended `clean_pod_evidence` columns:

| Group | Columns / content |
|---|---|
| File identity | `document_id`, `filename_system_version`, `filename_order_id`; derive from actual path, not the output record's top-level identity |
| Image observations | `extracted_system_version`, `extracted_order_id`, `delivered_at_raw`, `delivered_at_sgt`, `driver_code`, `delivered_to`, `received_by`, `remarks`, `signature_present`, `cod_on_card` |
| Confidence and status | Original `fields_json` including raw values/confidence, `flags_json`, `validation_json`, `status` and safe error details |
| Version/provenance | `run_id`, source hash via document FK, parser/prompt/model versions, extraction timestamp, original locator conventions |
| Approved association | Nullable `linked_system_version`, `linked_order_id`, `identity_status`, `link_reason`; set only after reconciling filename, image and order reference |

Keep signature presence nullable/uncertain; a detected mark does not identify the receiver. If no image extraction has occurred, store filename identity with `not_extracted` status and null content fields. If extraction fails, retain the failure rather than representing it as an absent source file. Never create a fabricated POD for v2.

**Important implementation detail:** `pod.normalise()` can replace the top-level `source_system`/`order_id` with the reference read from the image and flag a filename mismatch. A’s POD loader must independently retain filename identity; B reviews the linked order identity. It must not blindly attach the extraction to an order using only those top-level fields. Quarantine identity conflicts for review; failed/partial records still retain provenance.

## 6. Reconcile Ralph's implementation with the proposed tables

| Existing implementation / output | Proposed database mapping | Reuse and change required |
|---|---|---|
| `emails.py` → `emails.jsonl` | `clean_complaint_emails`; `meta_source_documents`; `meta_ingestion_runs` | Reuse body, categories, claims, candidates and locators. SQL loader is new. Email is not automatically a new complaint or a verified order link; compliments are not complaints. |
| `pod.py`, `extract_images.py` → `pod_records.jsonl` | `clean_pod_evidence`; document/run references | Reuse `fields`, confidence, flags, `validation` and extraction metadata. Preserve separate filename/image identity and select the current reviewed extraction deterministically. |
| `ratecard.py` → `rate_cards.jsonl` | `clean_rate_cards`, `clean_rate_prices`, `clean_rate_surcharges` | Reuse extraction, source locators and original notes. Add Q06 retrospective applicability and Q07 boundary interpretation without rewriting what the image says. |
| `policy.py` → `policy_chunks.jsonl` | Guide content → `clean_policy_rules`; retrieval-compatible chunks remain a derived output | Current discovery searches guide/policy/resolution filenames under `tabular/` or `docs/`; current formats are MD/TXT/CSV. It will not discover/read the guide embedded in the new case-log XLSX. Add explicit workbook/sheet extraction, preserving rows and general notes. No OCR is needed for native Excel text. |
| `manifest.json`, `image_manifest.json` and extraction cache | `meta_source_documents`, `meta_ingestion_runs`, versioned evidence payloads | Reuse hash/version/status metadata. Keep existing cache files; a DB import must not trigger another paid vision run. Preserve per-file failure outcomes. |
| `search.py` → `search_emails`, `search_policy` | Existing retrieval tools remain valid through adapters | Current search uses keyword ranking, not embeddings. Keep it initially; load the same reviewed records/chunks or add a DB-backed adapter with the same envelope and source locators. Do not build two conflicting corpora. |
| `pod.find_pod()` | B's MySQL-backed `get_pod` adapter | Preserve system-aware lookup and cited record shape. Audit failed versus partial handling: existing helper maps non-ok extractions to partial. New adapter must make actual extraction failures explicit. |
| `ratecard.lookup_rate()` | B's rate tool over reviewed card/price rows | Current helper rejects pre-April dates and returns ambiguous at shared edges. Those behaviours are superseded by the client answers; update code/contracts/evals before claiming the rate tool is client-compliant. |
| Existing A unit/eval cases | E's consolidated suite; A owns extraction expectations/fixes | Retain regression coverage, revise now-obsolete missing-guide/rate-edge expectations, and add XLSX guide, identity conflict, retrospective rate and exact-boundary cases. |

Ralph's `source_system` maps to the database's `system_version`; document this adapter rather than renaming every upstream field. Preserve the tool envelope (`ok`, status, data, sources, error) and exact citation locators. C verifies claim support; D renders evidence; E verifies integration. Stored unmasked records are restricted: C/B must apply agreed minimisation/masking before model/customer exposure.

## 7. Source paths and indexing

The original package is nested under `data/team2_merlion_express_package/`, but the new workbook is under `data/`. Ralph's CLI accepts one `--data` root and constructs source refs from that root. Register explicit configured inputs for the package, case workbook and client-answer workbook; do not assume a single directory scan will find all three. Resolve Ralph's logical `data/...` references through the manifest/input-root mapping to the actual existing file, while preserving source IDs/locators. Avoid renaming originals merely to make discovery work.

Required lookup indexes: composite order key; driver code; GPS `(driver_id, ts_utc)`; cases `(opened_at_sgt, reporting_zone)` and `(opened_at_sgt, driver_id)`; evidence by validated system/order and document/version; prices by card/zone/weight interval. Support joins with relational keys rather than substring matching JSON.

Use UTC `DATETIME` columns with explicit `_utc` names for normalised instants and retain raw epoch/local values and timezone provenance. Set connection timezone deliberately. Validate GPS alignment against the client's approximate 07:00–23:00 working window without deleting outliers automatically.

## 8. Queries and results that should remain derived

- Weekly complaint counts: canonical cases, agreed Date Opened interpretation and explicit week boundaries; include unknown attribution and duplicate exclusions. Follow-up text does not add a complaint.
- Policy compliance: compare historical resolution/refund/approval with reviewed rules and available facts. Distinguish compliant, potentially noncompliant and insufficient evidence. Approval thresholds mean recommend/escalate, not execute payments.
- Rate calculation: include confirmed standard service, applicable zone/weight, relevant surcharge inputs and GST. The amount actually paid may be unavailable; label reconstructed charges as calculated rather than a verified payment.
- Corporate escalation: count deduplicated complaints per account/month. Do not guess corporate-account identity from unrelated person names if no reliable link exists.
- Missing photos/proof of purchase, declared values or prior attempts remain unavailable evidence even after the guide arrives.

Use views or service queries first; do not add permanent weekly-summary, computed-charge or compliance-result tables solely to cache this small dataset. Add versioned assessments only if a review/export workflow needs durable results.

## 9. Unstructured storage, optional tables and runtime boundary

MySQL can hold text, JSON and binary data. There is no input here that is inherently impossible to store in MySQL. For this demo, keep original images/workbooks/PDFs as files; store paths/hashes, extracted facts and text in MySQL. This avoids needlessly storing image bytes twice while retaining verifiable evidence.

The Resolution Guide is a small native spreadsheet, so structured rule lookup and code checks are the initial choice. Embeddings are optional and must demonstrate a retrieval benefit. Retain Ralph's existing keyword retrieval initially; do not introduce a vector database as a prerequisite.

Optional additions, not part of the twenty-table baseline:

| Optional table / store | Create + load owner | Current code status | Add only when |
|---|---|---|---|
| `clean_document_chunks` | A / Ralph | Chunk files/keyword search exist; no MySQL DDL/loader | A DB-backed adapter needs versioned text/locators; otherwise retain generated chunk files |
| `clean_case_email_links` | B / Jenn Fang | No MySQL DDL/loader | Multiple verified emails must link to multiple cases; do not force ambiguous associations |
| `clean_case_policy_assessments` | C / John | No MySQL DDL/loader | Durable reviewed compliance results need rule/data versions and reviewer outcomes |
| Framework session/checkpointer tables (`meta_` prefix) | C / John | No MySQL session migrations/loader found | C selects MySQL-backed persistence with configurable prefixed table names; use its supported schema/migrations rather than renaming framework tables behind its back |
| Local embedding index (not a MySQL table) | A / Ralph | Keyword search exists; embedding index not implemented | A demonstrates benefit and supplies a reproducible, versioned index build/update procedure |

## 10. Delivery order and checks

1. B/C agree schema names, keys and source/citation adapters. Register inputs; preserve the existing instructor tables and source files within the single-database design.
2. B loads raw case rows and cleaned drivers/orders/latest deliveries, then canonical cases/member lineage. Validate 505 raw rows without claiming that means 505 distinct complaints. Record 45 missing source zones and 59 missing source drivers; review deduplication and mixed dates/money before reporting.
3. A adds the explicit Excel guide parser; A creates and loads guide/rate/POD/email tables without paid re-extraction; B reviews relational joins and consumes the loaded evidence. A/B update rate interpretation and tests from Q06/Q07. C implements deterministic policy checks and handles unsupported evidence honestly.
4. B loads/indexes GPS and reviewed town/pricing/CBD mappings; E creates/loads the sourced calendar with B/C review; verify time semantics and business derivations. Missing working-day/CBD mapping details remain documented decisions or targeted follow-up questions.
5. C connects tools to the reviewed tables/adapters; D displays cited evidence and Jeffrey reviews business usefulness. E integrates actual A/B/C/D cases into the shared suite and checks restart/reload behaviour.

Acceptance includes repeatable imports, no duplicate records on rerun, source-to-loaded reconciliation, native MySQL checks, system-aware joins, preserved conflicts, exact 3/10/25 kg handling, retrospective pricing authority, correct missing-v2-POD behaviour, guide citations, duplicate-case accounting and honest unknowns. Do not claim these have passed until executed.

This document specifies the data design and implementation gaps. It does not create tables, change Ralph's code, or certify a running MySQL database.

## 11. Owner delivery contract — creation and loading are one deliverable

The named owner in Section 3 must supply **both** versioned table/index/constraint creation and executable loading/transformation code. Producing a JSONL file, spreadsheet, SQL diagram or handoff alone does not finish a table deliverable. B coordinates relational keys and dependency ordering; C provides the shared connection/transaction/provenance utilities. A remains accountable for loading A-owned tables, rather than leaving all MySQL work to B.

Status above is based on the checked-out `backend/`, `database/`, `scripts/`, A's contracts and handoff, reviewed on 16 Nov. `database/` contains only a placeholder; A's `sqlref.py` reads the dump in memory, not MySQL. No application-table CREATE/ALTER or database-insert implementation was found. This is repository implementation status, not an inspection of any person's live MySQL server. A's reported extraction runs remain separate evidence, not proof of table loading.

### Required owner packages

Names below are proposed delivery locations, **not existing/runnable commands**. Owners may use SQL plus Python or migration/loader modules, provided the public setup and batch entry points are documented and equivalent. Do not create a different manual procedure per laptop.

| Owner | Required creation artifact | Required load artifact and responsibility | Review / objective |
|---|---|---|---|
| C / John | Shared database bootstrap and versioned migrations for `meta_source_documents`, `meta_ingestion_runs` | Shared connection/configuration, input registration, run lifecycle and orchestration helpers | B reviews keys; other loaders use the same metadata API. Credentials remain external. |
| B / Jenn Fang | Versioned migrations for B-owned raw-import and cleaned operational/case/GPS/zone tables; wrapper around instructor DDL for initial setup | Parameterised SQL-dump staging, Excel case import, cleaning/deduplication, GPS and mapping loaders | A/C review source joins; E verifies a teammate can run setup and process a later batch. Never edit the instructor dump itself. |
| A / Ralph | Versioned migrations for POD/policy/rate/email tables | MySQL adapters over existing JSONL/manifests; Excel guide extraction; corrected rate interpretation; source-aware upserts | B reviews keys/types, C reviews evidence/tool compatibility. Reuse cached extraction; do not repeat paid calls to populate MySQL. |
| E / Ho Wai Hong | Versioned migration for `clean_calendar_dates` | Parameterised calendar import/extension with source/year/version and validation | B/C review holiday and working-day semantics. E also executes cross-owner setup/batch acceptance; does not take over their loaders. |
| D / Jeffrey | No baseline data table assigned | Consume C's API; provide business scenarios and review output usefulness | No extra table invented solely to distribute ownership. |

Suggested locations: owner migrations under `database/migrations/`, owner loaders under a shared Python loading package, and the documented entry points under `scripts/`. C exposes one setup/batch orchestration interface that delegates to owner loaders; each owner supplies their component. Add migrations before loaders according to FKs, not the owner's letter. When implemented, record actual paths, commands, PR/commit, tested source version and check results beside the table status. All current application SQL-loader statuses remain pending.

### Each table owner must document and demonstrate

1. Dependencies and configuration; supported input file formats/columns; a synthetic fixture and actual command with explicit input paths. Support Docker-hosted or installed MySQL through connection configuration, not separate business logic.
2. Fresh database creation, loading the current package and count/key/provenance verification from another developer's machine.
3. Rerunning the same batch without duplicate business records, paid extraction or double-counted complaints.
4. Processing a changed/new batch, preserving earlier source evidence and showing inserted/updated/unchanged/rejected counts. Counts for A's multiple price/surcharge rows reconcile to their source records, not one row per file.
5. Missing columns, malformed values, unexpected schema/version and failed extraction produce actionable reports and a failing exit code where publication is unsafe. Unknown/partial evidence is not silently dropped.
6. Interrupted import rollback/retry, and protection against replacing a newer snapshot with an older one. No embedded secrets or client data in Git/CI.

## 12. Repeatable setup and periodic client batches

### First setup for any teammate

1. Install documented dependencies and configure the local MySQL connection. Obtain approved source files and extraction artifacts through the agreed channel.
2. Run the shared bootstrap/migration entry point. Create the original SQL source tables through B's wrapper, then C's metadata tables and other tables in dependency order. Preserve source files; normal setup must not automatically reset an already populated database.
3. Register the batch/input manifest and load operational data, raw cases and mappings; transform canonical cases and lineage. Load A's evidence/rules/emails and E's calendar, then enable tool/API queries.
4. Run owner checks and E's consolidated verification. Record actual outcomes. Current reference counts (40 drivers, 25,833 orders, 24,802 deliveries, 505 raw case rows) apply only to the current source version; future batches require their own controls, not hard-coded equality to these counts.

### Every later client batch

- **Identify the batch:** client/as-of identifier, receipt time, explicit source paths, hashes, source type, declared full snapshot or incremental update, and parser/mapping/policy versions. Reject ambiguous update semantics rather than infer them from the filename or file modification time.
- **Preserve originals:** store each version in an ignored batch directory before loading. New SQL dumps can contain DROP/CREATE statements: B uses a vetted importer with an isolated disposable staging area and validates, never blindly executes periodic dumps over the application's live tables or destroys the only raw snapshot.
- **Validate before publication:** check schema, types, source scope, reference keys and extraction outcomes. Stage owner outputs, reconcile counts and retain rejects/errors locally with safe summaries. Full snapshots and incremental feeds have different absence/deletion semantics; missing rows are not deletions unless explicitly agreed.
- **Apply stable keys:** source hash/version plus original row/line identifies raw evidence; composite system/order identifies orders; driver ID/code identifies drivers. Case No assists matching updates but does not replace complaint deduplication or prove a unique complaint. For an updated case, retain the prior raw row/source version and its association with the canonical case.
- **Handle repeated snapshots:** do not double-count cases/GPS/images seen in overlapping exports. GPS `(document_id, line_number)` only prevents replay of the identical file; B must also define an audited observation fingerprint/occurrence rule for overlap across different files, without discarding legitimate repeated observations. Preserve raw multiplicity when unsure.
- **Publish coherently:** C's orchestrator marks a batch validated/published only after required owner loads succeed. API/tools read the published batch/current views, not partially loaded staging results. Use transactions or versioned staging/promotion with restart-safe run records; failed runs retain diagnostics and never appear complete.
- **Avoid unnecessary work:** unchanged source hashes and unchanged transform versions are skipped/reused. Reprocess changed or failed sources deliberately. A distinguishes extraction/model versions from SQL loader versions; a schema reload does not require re-reading every image with a paid model.
- **Recheck the application:** owners run component checks; E verifies fresh setup, same-batch rerun, overlapping/new batch, interrupted run and source-cited complaint/weekly output. D reviews user-visible changes; C confirms policy/rate authority and session references remain valid against the intended published data.

New policy, rate or client-answer versions require explicit applicability/authority and revised tests; never automatically extend the current retrospective pricing permission or current guide policy to every future version. Late corrections to existing business keys need recorded precedence/as-of rules and provenance.

The objective is one documented, repeatable setup/batch workflow that **every teammate can run**, built from components whose owners are responsible for both DDL and loading. Until those artifacts and checks exist, this remains a delivery requirement rather than implemented functionality.
