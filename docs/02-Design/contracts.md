# Technical contracts

**Updated:** 16 Nov 2026. **Status:** Proposed minimum interfaces; C/John coordinates agreement by 17 Nov. These contracts are not implemented or frozen merely because they are documented. Supply versioned synthetic examples and executable checks as each interface lands.

| Boundary | Producer / owner | Consumer / reviewer | Minimum contract |
|---|---|---|---|
| POD/rate extraction | A/Ralph | B/Jenn Fang, C/John | Stable source ID/hash, original file locator, fields, candidate identity, uncertainty, processing version/status/error |
| Cleaned data and candidates | B/Jenn Fang | C/John | Composite system_version/order_id, distinct event IDs, candidate evidence, raw/normalised timestamps and assumptions |
| SQL/GPS/image tools | B; A supplies image extraction | C | Validated inputs; found/not_found/ambiguous/partial/failed; cited rows/files; safe retryable/nonretryable errors |
| Chunking/embedding/indexing and email/policy retrieval | A/Ralph | C; D reviews business relevance; E runs cases | Source-aware boundaries/overlap, source/date/system metadata, embedding/index version/cache, query/filter/ranking behaviour and cited original locators; missing guide remains unavailable |
| Complaint/session HTTP | C/John | D/Jeffrey, E/Wai Hong | Request/session IDs; workflow state, candidates/clarification, evidence/conflicts, recommendation or abstention, citations, safe errors |
| Weekly summary | B computes; C exposes | D/E | Reporting boundaries/timezone, complaint source/dedup/attribution definitions, driver/zone totals and unknown attribution |
| Session persistence | C | D/E verify | Stable session ID, messages/clarification/evidence references, workflow state; follow-up and restart recovery; isolation between sessions |
| Telemetry | C defines; A/B/C emit | E verifies | Linked request/tool events, latency, model/tokens/cost, errors and safe source references; avoid double counting extraction |
| Eval runner/cases | C supplies starter; E maintains; all contribute | Each case owner, C reviews | Case ID/category/owner, synthetic input or local-only fixture path, expected fields/content/refusal/sources, pass/fail and diagnostic component |

Route paths and concrete JSON schemas remain to be agreed, rather than guessed by the frontend. C provides normal, ambiguous, unavailable-source, refusal and error fixtures plus the first runnable API call. D implements React against those examples; E builds checks from them. Generic source_system/order_no API aliases must explicitly map to system_version/order_id.

## Common result and provenance rules

- Define how `ok` relates to each status. An empty successful query is not a failed dependency.
- Each citation contains source ID, type, original ref, locator and source record key where relevant. C checks returned references and claim support; D renders accessible references.
- A records uncertain OCR fields and failed inputs. B preserves uncertainty in loaded records and validates joins/calculations in code/SQL.
- Preserve raw timestamps and the evidence for timezone normalisation. No blanket correction or source hierarchy without validation.
- Missing case log, guide, historical rates or zone/service inputs produces explicit limitations; no invented policy or silently substituted complaint totals.
- Persisted state stays local/ignored. Model keys never enter frontend assets, fixtures, logs or Git.

## Acceptance / handoff

Producer and consumer review a synthetic example and failure case, record the agreed version, then link their PR and actual check results in `docs/03-Handoffs/`. E's first runner increment should execute five cases from C's starter; a 200 response alone is not a pass. Every owner fixes failures in their own component. Jeffrey contributes business scenarios/relevance review; Wai Hong owns runner implementation and consolidated results, not all expected-answer definitions. A/B/C validate source facts, identity and policy expectations.
