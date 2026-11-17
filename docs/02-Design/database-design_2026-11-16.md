# Database design and reconciliation with Developer A

**Updated:** 17 Nov 2026, SGT. **Status:** Proposed design; no database migrations or loader changes have been executed by this review.

## 1. Design decision

Use MySQL for structured facts, cleaned complaints, joins, calculations and evidence metadata. Keep original files and extraction caches under ignored `data/` and `output/`. Reuse Ralph's existing extraction records, provenance and retrieval tools rather than implementing a second extraction pipeline.

**Use one database: `merlion_express`, with separate raw and cleaned tables.** Keep the instructor’s `orders`, `drivers` and `deliveries` names unchanged. Prefix every new table by purpose: `raw_` for staged source rows, `clean_` for validated application data, and `meta_` for provenance/run metadata. Use `view_` for Gold/reporting views, not `vw_`. Database location does not define the data layer; raw, cleaned, metadata and reporting objects coexist in this database. Do not clean the instructor tables in place or restore a dump over application tables.

Raw preservation does not require a duplicate database table for every file. Keep the original workbook, JSONL, email and image files immutable. Use a raw case table because spreadsheet rows need explicit typing, cleaning and deduplication lineage. Use typed GPS rows with the original epoch and source line, retaining the original JSONL as raw evidence.

### Current phase versus future enhancement

**Current delivery:** retain instructor `orders`, `drivers`, `deliveries`; create only `raw_case_log`, `clean_cases`, `clean_case_members` and the two weekly reporting views. Ralph’s POD/rate/email/policy data stays in versioned files behind his existing tools. No SQL migration is required for A’s evidence in this phase. GPS and reviewed zone/calendar lookups can remain file-backed where their tools validate and query them correctly.

**Proposed final state:** retain the complete inventory below, but mark the other fourteen application tables **Future enhancement**. These are candidate enhancements if centralised querying, governance, scale or measured performance justifies them; they are not course blockers or a commitment to migrate everything. Optional tables/stores in Section 9 are also future/conditional. Current ownership requires code/scripts only for current objects; future owners retain responsibility if their enhancement is approved.

Current operation still requires client-confirmed policy/rate changes, guide ingestion, validated joins/calculations, persistent sessions, traceable batches and passing evals. Deferring SQL storage does not defer those behaviours. C’s session-persistence implementation is required, but a MySQL session table is only one storage option.

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

The complete proposed final-state inventory has three preserved instructor tables plus seventeen application tables. **Current scope is three new tables and two views; fourteen application tables are deferred to future enhancement.** Every final-state table keeps its purpose, owner and code status below. Optional additions are in Section 9.

### Bronze — preserved instructor tables in `merlion_express`

| Table | Purpose | Identity / treatment | Create + load owner | Phase | Current code status |
|---|---|---|---|---|---|
| `drivers` | Unmodified driver export | Existing `driver_id`; do not merge drivers by name | B / Jenn Fang | Current phase | Instructor dump contains DDL and data; manual seeding commands exist. Automated periodic-batch importer not implemented. |
| `orders` | Unmodified order export | Raw instructor table lacks a declared primary key; `(system_version, order_id)` is unique in the supplied dump | B / Jenn Fang | Current phase | Instructor dump contains DDL and data; manual seeding commands exist. Automated periodic-batch importer not implemented. |
| `deliveries` | Unmodified latest-attempt export | Existing `delivery_id`; not a complete delivery-event history | B / Jenn Fang | Current phase | Instructor dump contains DDL and data; manual seeding commands exist. Automated periodic-batch importer not implemented. |


### New prefixed tables in `merlion_express`

| Table | Purpose | Primary identity and main relationships | Create + load owner | Phase | Current code status |
|---|---|---|---|---|---|
| `meta_source_documents` | Register originals and source versions: relative path, hash, type and logical source ID | `document_id`; unique `(relative_path, sha256)`; preserve Ralph's source ID as an external identifier | C / John | Future enhancement | No MySQL DDL/loader. A’s file hashes/manifests are reusable inputs. |
| `meta_ingestion_runs` | Record loader/parser/model/prompt versions, start/end, outcomes, counts and configuration hash | `run_id`; common `batch_id`, optional `parent_run_id`, component, stage/publication status and source manifest; referenced by loaded/extracted records; no credentials in configuration | C / John | Future enhancement | No MySQL DDL/loader. A’s manifests/telemetry exist as files. |
| `raw_case_log` | Lossless staged case-log rows before cleaning, including source values/types and parse issues | `raw_case_id`; current unique `(source_file_hash, sheet_name, row_number)` with inline source/batch fields; future document/run FKs after migration | B / Jenn Fang | Current phase | No MySQL DDL/loader; received XLSX must be parsed. |
| `clean_drivers` | Validated driver IDs/codes used by case attribution and GPS joins | `driver_id`; validated unique `driver_code`; source reference | B / Jenn Fang | Future enhancement | No cleaned-table DDL/loader; raw source exists. |
| `clean_orders` | Cleaned orders with original identity, validated dates/postal strings and standard-service provenance | Composite PK `(system_version, order_id)`; source reference; zone assignments reference reviewed mapping | B / Jenn Fang | Future enhancement | No cleaned-table DDL/loader; raw source exists. |
| `clean_deliveries_latest` | Cleaned most recent recorded attempt per order, preserving raw local time and derived UTC | `delivery_id`; unique `(system_version, order_id)` for this export; FK to orders and driver | B / Jenn Fang | Future enhancement | No cleaned-table DDL/loader; raw source exists. |
| `clean_cases` | One canonical complaint, cleaned fields, historical action/refund/voucher, resolved order/driver/zone and resolution status | `case_id`; nullable logical system/order and driver references to instructor data now; future FKs to cleaned operational tables; unresolved identity stays explicit | B / Jenn Fang | Current phase | No MySQL DDL/loader or canonical-case pipeline. |
| `clean_case_members` | Map every original case-log row to its canonical complaint, with deduplication rule/version/reason | `raw_case_id` as PK/FK, `case_id` FK; multiple source rows may map to one case; no silent deletion | B / Jenn Fang | Current phase | No MySQL DDL/loader or persisted deduplication lineage. |
| `clean_gps_pings` | Queryable driver/time/location observations with raw epoch, normalised UTC and alignment provenance | `ping_id`; driver FK; `(document_id, line_number)` unique; index `(driver_id, ts_utc)` | B / Jenn Fang | Future enhancement | No MySQL DDL/loader; JSONL source exists. |
| `clean_pod_evidence` | Versioned image extraction and filename identity, field confidence, SQL comparisons and conflicts | `pod_id`; document/run FKs; unique `(document_id, extraction_version)`; nullable validated order FK | A / Ralph | Future enhancement | Image extraction/JSONL exists; MySQL DDL/loader not implemented. |
| `clean_policy_rules` | Source guide rows and general notes, conditions, limits and required approval roles | `policy_rule_id`; document/worksheet row locator, guide version and authority references; code enforces reviewed rules | A / Ralph | Future enhancement | MD/TXT/CSV parsing exists; Excel guide support and MySQL DDL/loader not implemented. |
| `clean_rate_cards` | Source card, currency, printed effective date, extracted notes and client-approved applicability | `rate_card_id`; source/run FKs; authority document and Q06 locator for retrospective use | A / Ralph | Future enhancement | Image extraction/JSONL exists; MySQL DDL/loader and clarified applicability changes pending. |
| `clean_rate_prices` | Structured standard price per pricing zone and non-overlapping weight interval | `rate_price_id`; card FK; unique `(rate_card_id, pricing_zone, min_kg, max_kg)`; explicit inclusive/exclusive bounds | A / Ralph | Future enhancement | Extracted price rows exist; MySQL DDL/loader and confirmed boundary handling pending. |
| `clean_rate_surcharges` | Card surcharge/fee formulas, applicability, availability and required inputs | `surcharge_id`; card FK; source locator; typed amount/percent/minimum where applicable plus original rule text | A / Ralph | Future enhancement | Extracted surcharge records/notes exist; MySQL DDL/loader not implemented. |
| `clean_zone_mapping` | Reviewed town mapping to operations zone, pricing zone, special-area treatment and CBD district classification where known | `mapping_id`; reviewed normalised town/match rule; authority, mapping version and review status; unknowns remain explicit | B / Jenn Fang | Future enhancement | No MySQL DDL/loader or approved mapping seed implemented. |
| `clean_calendar_dates` | Relevant Singapore dates, public-holiday flags and documented working-day treatment | Date PK; calendar source/version; do not invent Saturday/working-day rules where unspecified | E / Ho Wai Hong | Future enhancement | No MySQL DDL/loader or sourced calendar seed implemented; B/C review rules. |
| `clean_complaint_emails` | Ralph's parsed email records, original body/claims/locators and optional verified case association | `email_id`; document FK; unique source document; nullable case FK; retain multiple order-number candidates in JSON | A / Ralph | Future enhancement | Email parser/search/JSONL exists; MySQL DDL/loader not implemented. |



In the proposed final-state design, there is no additional `rates` or `raw_pod` table: `clean_rate_cards`/`clean_rate_prices`/`clean_rate_surcharges` and the original images plus `clean_pod_evidence` cover those responsibilities. The earlier suggested `rate_rules` and `public_holidays` names are replaced by this explicit inventory.

### Naming and layer rules

| Layer / purpose | Prefix | Examples | Meaning |
|---|---|---|---|
| Bronze | `raw_` | `raw_case_log` | Source-preserving staging rows; instructor tables are the only naming exceptions |
| Silver | `clean_` | `clean_orders`, `clean_cases`, `clean_pod_evidence` | Validated facts, evidence, mappings and rules; a clean evidence row can still carry uncertainty/conflicts |
| Gold | `view_` | `view_weekly_complaints_by_driver` | Business queries over reviewed data; views do not store separate copies of results |
| Shared metadata | `meta_` | `meta_source_documents`, `meta_ingestion_runs` | Source/run lineage and publication control; not a Silver business layer |

Final-state PK/FK references and loader queries use the prefixed target names. Relationships to deferred tables apply only when those enhancements are implemented. For example, `clean_deliveries_latest` references `clean_orders` and `clean_drivers`; `clean_case_members` links `raw_case_log` to `clean_cases`; extraction tables reference `meta_source_documents` and `meta_ingestion_runs`. Preserve Ralph's filenames (`rate_cards.jsonl`, `pod_records.jsonl`, `emails.jsonl`), Python module/tool names and field contracts: table prefixes are applied by the SQL adapters only.

### Current-phase keys without future-table dependencies

- `raw_case_log` stores batch/source identifiers, workbook relative path, file hash, sheet, row, source values/types and parse status inline. Unique `(source_file_hash, sheet_name, row_number)` prevents replay of the same source. It does not require `meta_source_documents` or `meta_ingestion_runs` to exist. Record batch/transform history in a versioned manifest.
- `clean_cases` stores canonical identity, cleaned date/category/money, nullable resolved `system_version`/`order_id`, driver ID and reviewed reporting zone with mapping/version provenance. Resolve against existing instructor tables with code-validated composite joins; do not require `clean_orders` or `clean_drivers`. The raw `orders` table lacks a composite PK, so do not assume an enforceable FK exists there.
- `clean_case_members` has actual FKs to the current `raw_case_log` and `clean_cases` tables and records matching/deduplication reasons and versions. Keep raw-to-canonical lineage across batches.
- Zone/calendar rules come from reviewed, versioned lookup files; metadata comes from manifests. Unknown attribution and uncertain identity stay explicit. If a future SQL representation is introduced, add/backfill its FKs and reconcile it against the existing file source before switching tools.

### Current-phase Gold views (not additional physical tables)

| View | Purpose | Create owner | Phase | Current code status |
|---|---|---|---|---|
| `view_weekly_complaints_by_driver` | Deduplicated weekly complaints by stable driver ID, including unknown attribution | B / Jenn Fang | Current phase | Not implemented; owner supplies CREATE VIEW migration and check queries |
| `view_weekly_complaints_by_zone` | Deduplicated weekly complaints across the five operations zones, including unknown attribution | B / Jenn Fang | Current phase | Not implemented; owner supplies CREATE VIEW migration and check queries |

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

**Future enhancement only:** recommended `clean_pod_evidence` columns. Current-phase tools use the equivalent fields in Ralph’s JSONL records; no SQL table is required.

| Group | Columns / content |
|---|---|
| File identity | `document_id`, `filename_system_version`, `filename_order_id`; derive from actual path, not the output record's top-level identity |
| Image observations | `extracted_system_version`, `extracted_order_id`, `delivered_at_raw`, `delivered_at_sgt`, `driver_code`, `delivered_to`, `received_by`, `remarks`, `signature_present`, `cod_on_card` |
| Confidence and status | Original `fields_json` including raw values/confidence, `flags_json`, `validation_json`, `status` and safe error details |
| Version/provenance | `run_id`, source hash via document FK, parser/prompt/model versions, extraction timestamp, original locator conventions |
| Approved association | Nullable `linked_system_version`, `linked_order_id`, `identity_status`, `link_reason`; set only after reconciling filename, image and order reference |

Keep signature presence nullable/uncertain; a detected mark does not identify the receiver. If no image extraction has occurred, store filename identity with `not_extracted` status and null content fields. If extraction fails, retain the failure rather than representing it as an absent source file. Never create a fabricated POD for v2.

**Important implementation detail:** `pod.normalise()` can replace the top-level `source_system`/`order_id` with the reference read from the image and flag a filename mismatch. The future A-owned POD SQL loader must independently retain filename identity; B reviews the linked order identity. It must not blindly attach the extraction to an order using only those top-level fields. Quarantine identity conflicts for review; failed/partial records still retain provenance.

## 6. Reconcile Ralph's implementation with current tools and future tables

| Existing implementation / output | Future database mapping / current contract | Reuse and change required |
|---|---|---|
| `emails.py` → `emails.jsonl` | `clean_complaint_emails`; `meta_source_documents`; `meta_ingestion_runs` | Reuse body, categories, claims, candidates and locators. Keep file-backed retrieval now; SQL loader is future work. Email is not automatically a new complaint or a verified order link; compliments are not complaints. |
| `pod.py`, `extract_images.py` → `pod_records.jsonl` | `clean_pod_evidence`; document/run references | Reuse `fields`, confidence, flags, `validation` and extraction metadata. Preserve separate filename/image identity and select the current reviewed extraction deterministically. |
| `ratecard.py` → `rate_cards.jsonl` | `clean_rate_cards`, `clean_rate_prices`, `clean_rate_surcharges` | Reuse extraction, source locators and original notes. Add Q06 retrospective applicability and Q07 boundary interpretation without rewriting what the image says. |
| `policy.py` → `policy_chunks.jsonl` | Guide content → `clean_policy_rules`; retrieval-compatible chunks remain a derived output | Current discovery searches guide/policy/resolution filenames under `tabular/` or `docs/`; current formats are MD/TXT/CSV. It will not discover/read the guide embedded in the new case-log XLSX. Add explicit workbook/sheet extraction, preserving rows and general notes. No OCR is needed for native Excel text. |
| `manifest.json`, `image_manifest.json` and extraction cache | `meta_source_documents`, `meta_ingestion_runs`, versioned evidence payloads | Reuse hash/version/status metadata. Keep existing cache files; a DB import must not trigger another paid vision run. Preserve per-file failure outcomes. |
| `search.py` → `search_emails`, `search_policy` | Existing retrieval tools remain valid through adapters | Current search uses keyword ranking, not embeddings. Keep it initially; load the same reviewed records/chunks or add a DB-backed adapter with the same envelope and source locators. Do not build two conflicting corpora. |
| `pod.find_pod()` | Current: A file-backed POD tool; future: B query adapter over A-loaded SQL evidence | Preserve system-aware lookup and cited record shape. Audit failed versus partial handling: existing helper maps non-ok extractions to partial. Current tool and any future adapter must make actual extraction failures explicit. |
| `ratecard.lookup_rate()` | Current: reviewed file-backed rate tool; future: B query adapter over A-loaded rate tables | Current helper rejects pre-April dates and returns ambiguous at shared edges. Those behaviours are superseded by the client answers; update code/contracts/evals before claiming the rate tool is client-compliant. |
| Existing A unit/eval cases | E's consolidated suite; A owns extraction expectations/fixes | Retain regression coverage, revise now-obsolete missing-guide/rate-edge expectations, and add XLSX guide, identity conflict, retrospective rate and exact-boundary cases. |

Ralph's `source_system` maps to the database's `system_version`; document this adapter rather than renaming every upstream field. Preserve the tool envelope (`ok`, status, data, sources, error) and exact citation locators. C verifies claim support; D renders evidence; E verifies integration. Stored unmasked records are restricted: C/B must apply agreed minimisation/masking before model/customer exposure.

## 7. Source paths and indexing

The original package is nested under `data/team2_merlion_express_package/`, but the new workbook is under `data/`. Ralph's CLI accepts one `--data` root and constructs source refs from that root. Register explicit configured inputs for the package, case workbook and client-answer workbook; do not assume a single directory scan will find all three. Resolve Ralph's logical `data/...` references through the manifest/input-root mapping to the actual existing file, while preserving source IDs/locators. Avoid renaming originals merely to make discovery work.

Current SQL indexes are for case dates, driver and zone reporting; existing source lookups must use composite system/order identity. For the future SQL expansion, planned lookup indexes include: composite order key; driver code; GPS `(driver_id, ts_utc)`; cases `(opened_at_sgt, reporting_zone)` and `(opened_at_sgt, driver_id)`; evidence by validated system/order and document/version; prices by card/zone/weight interval. Support joins with relational keys rather than substring matching JSON.

Use UTC `DATETIME` columns with explicit `_utc` names for normalised instants and retain raw epoch/local values and timezone provenance. Set connection timezone deliberately. Validate GPS alignment against the client's approximate 07:00–23:00 working window without deleting outliers automatically.

## 8. Queries and results that should remain derived

- Weekly complaint counts: canonical cases, agreed Date Opened interpretation and explicit week boundaries; include unknown attribution and duplicate exclusions. Follow-up text does not add a complaint.
- Policy compliance: compare historical resolution/refund/approval with reviewed rules and available facts. Distinguish compliant, potentially noncompliant and insufficient evidence. Approval thresholds mean recommend/escalate, not execute payments.
- Rate calculation: include confirmed standard service, applicable zone/weight, relevant surcharge inputs and GST. The amount actually paid may be unavailable; label reconstructed charges as calculated rather than a verified payment.
- Corporate escalation: count deduplicated complaints per account/month. Do not guess corporate-account identity from unrelated person names if no reliable link exists.
- Missing photos/proof of purchase, declared values or prior attempts remain unavailable evidence even after the guide arrives.

Use views or service queries first; do not add permanent weekly-summary, computed-charge or compliance-result tables solely to cache this small dataset. Add versioned assessments only if a review/export workflow needs durable results.

## 9. Unstructured storage, optional tables and runtime boundary

MySQL can hold text, JSON and binary data. There is no input here that is inherently impossible to store in MySQL. For the current phase, keep original images/workbooks/PDFs and Ralph’s extracted evidence as files; store case data and its inline provenance in MySQL. Migrating other extracted facts/text and shared metadata to MySQL is a future enhancement. This avoids needlessly storing image bytes twice while retaining verifiable evidence.

The Resolution Guide is a small native spreadsheet, so structured rule lookup and code checks are the initial choice. Embeddings are optional and must demonstrate a retrieval benefit. Retain Ralph's existing keyword retrieval initially; do not introduce a vector database as a prerequisite.

Additional future/conditional enhancements, outside the twenty-table final-state inventory:

| Optional table / store | Create + load owner | Phase | Current code status | Add only when |
|---|---|---|---|---|
| `clean_document_chunks` | A / Ralph | Future / conditional | Chunk files/keyword search exist; no MySQL DDL/loader | A DB-backed adapter needs versioned text/locators; otherwise retain generated chunk files |
| `clean_case_email_links` | B / Jenn Fang | Future / conditional | No MySQL DDL/loader | Multiple verified emails must link to multiple cases; do not force ambiguous associations |
| `clean_case_policy_assessments` | C / John | Future / conditional | No MySQL DDL/loader | Durable reviewed compliance results need rule/data versions and reviewer outcomes |
| Framework session/checkpointer tables (`meta_` prefix) | C / John | Future / conditional | No MySQL session migrations/loader found | C selects MySQL-backed persistence with configurable prefixed table names; use its supported schema/migrations rather than renaming framework tables behind its back |
| Local embedding index (not a MySQL table) | A / Ralph | Future / conditional | Keyword search exists; embedding index not implemented | A demonstrates benefit and supplies a reproducible, versioned index build/update procedure |


## 10. Current-phase delivery order and checks

1. B preserves/imports the three instructor source tables through the existing [setup guide](../../database/createdb_seed_sql_data.md), then creates `raw_case_log`, `clean_cases`, `clean_case_members` and the two `view_` definitions. Do not create the fourteen future tables as prerequisites.
2. B loads all case-log rows unchanged, applies reviewed cleaning/identity/deduplication rules, and records lineage. Use manifests and inline source fields instead of foreign keys to nonexistent future metadata tables. Validate 505 source rows for this workbook version without assuming 505 distinct complaints.
3. A retains existing cached JSONL/manifests and file-backed search/POD/rate tools. Add explicit Excel guide parsing and update Q06/Q07 rate behaviour/contracts/evals. Preserve uncertainty, exact citations and filename/image identity distinctions. Do not repeat paid extraction merely to integrate with MySQL.
4. B provides question-time SQL operational/case tools, a validated GPS-window tool and reviewed file-based zone/calendar derivations; E maintains the sourced calendar files with B/C review. C orchestrates SQL and file tools by explicit identifiers; joins and arithmetic are code/SQL, not model guesses.
5. C links a versioned manifest to the published SQL dataset and A's output versions. D displays cited answers/reporting; E verifies source joins, counts, failure handling, new-batch processing and restart/session behaviour.

Acceptance includes repeatable imports, no duplicate complaints on rerun, raw-to-clean reconciliation, preserved conflicts, correct 3/10/25 kg boundaries, retrospective rate authority, honest missing-v2-POD handling, guide citations, unknown attribution and reviewed policy outcomes. Do not claim checks passed until executed.

## 11. Owner delivery contract — scoped by phase

For each **current-phase** SQL object, its owner supplies both versioned DDL/index/constraint creation and executable load/transform code. Views require CREATE VIEW and verification queries, not an independent loader. Future-table owners supply equivalent artifacts only when their enhancement is approved; they are not current checkpoint obligations.

Implementation status was checked against the repository on 17 Nov: the database folder contains setup documentation but no application-table migrations/loaders; A supplies extraction/search/JSONL/manifests, not MySQL loading. This is repository status, not verification of anyone's live database. Existing extraction runs are not proof that a SQL table exists.

| Owner | Current-phase delivery | Future enhancement ownership | Verification |
|---|---|---|---|
| B / Jenn Fang | Creation/load/transform of `raw_case_log`, `clean_cases`, `clean_case_members`; two weekly `view_` definitions; source import, identity/zone rules and operational/GPS tools | Cleaned operational/GPS/zone tables and optional case-email linking | Native MySQL counts, reviewed deduplication lineage, source-aware joins, fresh setup and repeated/new-batch checks |
| A / Ralph | Existing file-backed POD/rate/email/policy tools, Excel guide parser, client-rule corrections, versioned cached outputs and parameterised batch processing | SQL evidence/policy/rate/email/chunk tables | No current SQL migration required; citation, extraction/failure, boundary/rate and source-version checks still required |
| C / John | Shared configuration, APIs/agent, policy checks, manifest-based orchestration/publication and persistent sessions using an appropriate store | `meta_source_documents`, `meta_ingestion_runs`, optional assessments and MySQL checkpointer integration | SQL/file version consistency, failure/recovery, claim support and secrets protection |
| E / Ho Wai Hong | Sourced/versioned calendar lookup files; consolidated evals and teammate setup/batch verification | `clean_calendar_dates` | B/C review calendar/working-day semantics; owners fix their own failed checks |
| D / Jeffrey | Frontend/reporting integration, business scenarios and presentation | No data table assigned | Visible definitions, unknowns and useful source-cited results |

Suggested delivery locations remain `database/migrations/` for current DDL and a shared Python loading package for loaders, with actual commands documented under `database/` or `scripts/`. These locations are proposed, not evidence of implemented commands. Each owner documents dependencies, inputs/configuration, versioned outputs, commands, actual tests and PR/commit. Current phase must not depend on an unimplemented future migration.

## 12. Repeatable setup and periodic client batches

### First setup for any teammate

1. Install documented dependencies; configure Docker-hosted or installed MySQL and obtain source files/cached extraction through the approved channel.
2. Preserve/import original SQL tables without editing the instructor dump. Apply the three current table migrations and two views. Do not reset populated application tables during normal setup.
3. Register a file-based batch manifest; load raw cases, transform canonical complaints/member lineage, and build/reuse A's versioned file outputs. Configure source roots explicitly for the original package, case workbook and client replies.
4. Validate source/SQL/file versions together before publication. E repeats the procedure on another setup; owners supply their own checks. Current reference counts apply only to the current source version, not every future batch.

### Every later client batch

- **Identify and preserve:** record client/as-of ID, hashes, input paths, full-snapshot/incremental semantics, parser/rule versions and receipt time in a versioned manifest. Preserve original files; do not infer precedence from filenames or file modification time.
- **Load safely:** SQL dumps contain DROP/CREATE instructions. B uses a vetted isolated staging/import procedure, not blind execution against live application tables. Full snapshots and incremental feeds have different absence/deletion semantics; absent records are not automatically deletions.
- **Preserve raw multiplicity:** identical-file replay is idempotent, but duplicate complaint evidence remains in raw storage. Case No aids update matching; it does not replace business deduplication. Retain prior raw versions and canonical membership history.
- **Handle overlap:** repeated snapshots must not double-count cases or GPS observations. File/line identity prevents replay of the identical file only; B defines audited cross-file matching/occurrence rules while retaining raw evidence.
- **Reuse extraction:** unchanged source/configuration hashes reuse A's cache. Only changed/failed inputs are reprocessed deliberately. A SQL reload never automatically triggers a full paid image run.
- **Validate and publish:** reconcile staged SQL transformations and immutable file outputs; C publishes one manifest linking approved versions. Queries read only a published SQL/file combination. Use transactions/versioned staging and restart-safe run logs; an interrupted run never becomes a completed batch. Metadata tables are not required for this behaviour.
- **Check the result:** owners supply checks; E tests fresh setup, same-batch rerun, overlapping/new batch, invalid schema, interrupted publication and source-cited complaint/weekly output. D reviews user-visible results. Rule changes trigger explicit transformation/test runs, not per-request source cleaning.

Later policy/rate versions require explicit authority/applicability; do not extend today's retrospective permissions to future cards automatically. Missing source facts remain unknown. New SQL representation is an enhancement, not a workaround for unavailable evidence.

## 13. Future enhancement promotion gate

Promote any deferred table only after a measured need, owner review and time/budget agreement. Typical reasons: indexed GPS queries outperform the file tool, persistent central provenance is needed, repeated SQL evidence joins become common, or an audited review workflow needs durable assessments. Do not migrate solely for uniformity.

The owner then delivers DDL, source-preserving loader/backfill, idempotency and new-batch checks, source/citation compatibility, count reconciliation and a documented cutover. Existing JSONL/tool contracts are preserved through adapters; do not maintain two conflicting authoritative copies. Add final-state FKs only after referenced tables exist and backfill has passed checks. Future SQL metadata can import existing manifest history.

This document changes design scope and ownership instructions only. No tables, views, loaders or paid image runs were created/executed by this documentation update.
