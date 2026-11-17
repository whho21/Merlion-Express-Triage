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
---

## A — Extraction records, search results and citations (DRAFT for the 17 Nov sync)

**Proposed by:** Ralph (Developer A). **Status:** draft for B/C review, not frozen. Section 4 matches the email
parser in `backend/unstructured/` (16 Nov).
**Consumers:** B (loads POD/rate records into MySQL), C (search tools, final-answer citation checks).
All samples are **synthetic**: no client data.

### 1. Citation (shared by every A tool)

Follows the team plan's citation shape, with A's locators filled in.

```json
{
  "source_id": "pod:v1:20095",
  "type": "image",
  "ref": "data/images/proof_of_delivery/POD_v1_20095.jpg",
  "locator": "field:date_time",
  "record_key": {"source_system": "v1", "order_id": 20095}
}
```

| `type` | `source_id` pattern | `ref` | `locator` |
|---|---|---|---|
| `image` (POD) | `pod:<v1|v2>:<order_id>` | image path | `field:<name>` |
| `image` (rate card) | `ratecard:<effective_from>` | image path | `row:<zone>/col:<band>` |
| `document` (email) | `email:<file stem>` | email path | `header:<name>` or `body:char:<start>-<end>` |
| `document` (policy) | `policy:<file stem>` | guide path | `section:<heading>` / `page:<n>` (format unknown until the guide arrives) |

### 2. POD extraction record (A produces → B loads)

Built by `python -m backend.unstructured.extract_images` → `output/unstructured/pod_records.jsonl` (git-ignored,
unmasked). Synthetic sample:

```json
{
  "source_id": "pod:v1:99999",
  "type": "image",
  "image_ref": "data/images/proof_of_delivery/POD_v1_99999.jpg",
  "image_sha256": "…",
  "source_system": "v1",
  "order_id": 99999,
  "fields": {
    "order_ref":    {"value": "V1-99999",         "raw": "V1-99999",          "confidence": "high"},
    "delivered_at": {"value": "2025-10-02T16:16", "raw": "O2/10/2025 16:16",  "tz": "Asia/Singapore (assumed)", "confidence": "medium"},
    "driver_code":  {"value": "DRV000",           "raw": "DRV000",            "confidence": "high"},
    "delivered_to": {"value": "Blk 000 Test Street #00-00 Singapore 000000",  "confidence": "high"},
    "postal_code":  {"value": "000000", "confidence": "high"},
    "block":        {"value": "000",    "confidence": "high"},
    "received_by":  {"value": "A. Tan (synthetic)", "kind": "name|role|blank", "role": null, "confidence": "high"},
    "signature":    {"value": "present|absent", "confidence": "high"},
    "remarks":      {"value": "COD collected $10", "confidence": "high"},
    "cod_on_card":  {"value": 10.0, "currency": "SGD", "confidence": "high"}
  },
  "template": "hotline_footer|thankyou_footer|unknown",
  "flags": ["lookalike_repaired:delivered_at", "cod_conflict_with_sql"],
  "notes": null,
  "validation": {"matches_sql": {"order": true, "delivered_at": true, "driver": true, "postal_code": true, "block": true},
                 "cod": {"card": 10.0, "sql": 0.0, "conflict": true}},
  "extraction": {"method": "vision", "model": "gpt-4o-mini", "prompt_version": "pod-v1",
                 "extracted_at": "2026-11-18T02:00:00+00:00", "cache": "hit|miss", "status": "ok",
                 "usage": {"prompt_tokens": 0, "completion_tokens": 0}},
  "status": "ok"
}
```

Rules:
- The model only copies text; **code** decides confidence: `high` = right format as printed · `medium` = right
  format only after a look-alike fix (I/l/| → 1, O/o → 0), always flagged `lookalike_repaired:<field>` (T-A13) ·
  `low` = missing/unreadable/wrong format, `value: null`, flagged `low_confidence:<field>`. Never guessed.
- `raw` keeps the printed text; `value` is normalised (dates day-first, T-A12).
- `validation.matches_sql` per field: `true`/`false`, `null` = nothing to compare. A mismatch adds
  `sql_mismatch:<field>` and makes the record `partial`. `cod.conflict`: `true` (amounts differ) or
  `"sql_cod_not_on_card"`; both add `cod_conflict_with_sql` (T-A08: show both values, never pick one).
- Other flags: `remark_contradicts_signature` ("left outside" but signed), `remark_contradicts_receiver` (remark
  says neighbour, receiver is another ROLE such as mum/front desk — T-A09), `signature_absent_verify_by_eye` (an
  "absent" signature is never trusted on the model's word: signature `confidence: "medium"`),
  `model_unreadable:<key>`, `order_ref_differs_from_file_name`.
- A signature means "card signed", not proof of who received it. `received_by.kind` = name/role/blank (T-A10).
  Stored unmasked (B/C/D mask — John, 16 Nov). Committed samples stay synthetic.
- `status`: `ok` · `partial` (a key field low, or an SQL mismatch) · `failed` (all key fields unreadable, or the model
  call failed — `extraction.error` says why). Every image gets a record and an `image_manifest.json` entry.
- `pod.find_pod(records, source_system, order_id)` returns `not_found` for a v2 order — a v1 card is never reused (T-A05).

### 3. Rate card record (A produces → B loads)

Built by the same command → `output/unstructured/rate_cards.jsonl`. Synthetic prices:

```json
{
  "source_id": "ratecard:2026-04-01",
  "type": "image",
  "image_ref": "data/images/rate_cards/rate_card_apr2026.jpg",
  "image_sha256": "…",
  "effective_from": "2026-04-01", "effective_to": null, "supersedes_previous": true,
  "currency": "SGD",
  "bands": [{"band": "<=3kg", "min_kg": 0.0, "max_kg": 3.0, "boundary_rule": "upper limit inclusive: min < weight <= max (client Q07)"}],
  "rows": [{"zone": "Central", "band": "<=3kg", "min_kg": 0.0, "max_kg": 3.0, "boundary_rule": "upper limit inclusive: min < weight <= max (client Q07)",
            "price": 0.00, "locator": "row:Central/col:<=3kg"}],
  "surcharges": [{"name": "same_day", "zone": "Central", "amount": 0.00, "available": true, "raw": "+$0.00"},
                 {"name": "CBD ERP hours (0730-1900)", "band": "<=3kg", "amount": 0.00}],
  "notes": {"raw": ["…every line under the table…"], "cod_handling": {"pct": 0.0, "min": 0.0},
            "reattempt_fee": {"amount": 0.0, "from_attempt": 3}, "gst_included": false, "gst_pct": 9.0,
            "corporate_rebate": {"pct": 0.0, "above_parcels_per_month": 0}, "public_holiday_rule": "…"},
  "status": "ok", "issues": [], "extraction": {"…": "as POD"}
}
```

`ratecard.lookup_rate(cards, zone=, weight_kg=, on_date=)` (for B's `get_rate`) returns the tool envelope.
**Updated 17 Nov for the client's answers** (the record keeps what the image prints; rules apply at lookup):
- **Q06:** a date before 2026-04-01 is priced from the April card with `applied_retrospectively: true` and the note
  "rate card applied retrospectively, per client (Q06…)". Only cards listed in `RETROSPECTIVE_AUTHORITY` are
  back-dated; a future card is not, so it returns `not_found` (T-A15).
- **Q07:** upper limit inclusive: `0 < w <= 3`, `3 < w <= 10`, `10 < w <= 25`. Exactly 3 kg → `<=3kg`, 10 kg →
  `3-10kg`, 25 kg → `10-25kg`. Over 25 kg or ≤ 0 → `not_found` with the reason (quoted by hand) (T-A16).
- **Q08:** every order is standard delivery (note on every result). CBD-ERP surcharge (CBD postal district and
  07:30–19:00) and public holidays (SG calendar) are not applied here — whoever builds the quote adds them.
- **Q03:** `zone` may be a price row ("East / North-East") or an ops zone ("North-East", "East", "North", "West",
  "Central", "Sentosa", "Jurong Island"); the ops zone comes from the town in the delivery address (B).
- `found` → `data: {price, currency, gst_included: false, band, price_zone, zone_input, boundary_rule,
  applied_retrospectively, notes, citation}`; the citation locator is `row:<zone>/col:<band>`.

### 4. Email record (A produces → C consumes via `search_emails`)

Built by `python -m backend.unstructured.ingest` → `output/unstructured/emails.jsonl` (git-ignored). **Unmasked**
(John, 16 Nov: A extracts everything; B/C/D mask). Synthetic sample:

```json
{
  "source_id": "email:2026-01-01_000",
  "type": "document",
  "ref": "data/docs/complaint_emails/2026-01-01_000.txt",
  "parser_version": "emails-1.0",
  "status": "ok",
  "issues": [],
  "received_at": "2026-01-01T10:00:00+08:00",
  "sender": "someone@example.com",
  "to": "support@example.com",
  "subject": "Wrong address delivered",
  "category": "wrong_address|missing_item|where_is_parcel|cod_wrong|late|thrown_over_gate|compliment|unclassified",
  "is_complaint": true,
  "order_numbers": ["99999"],
  "system_hint": null,
  "more_orders_unspecified": false,
  "claims": {"stay_block": "111", "pod_block": "222", "days_ago": null, "amount_extra": null, "status_claimed": null},
  "driver_codes": [],
  "corporate_account": null,
  "pii_detected": {"block": 2},
  "body": "You delivered my parcel to the wrong block!! I stay blk 111 but the POD photo shows blk 222. Order 99999. Please retrieve ASAP.\n",
  "locators": {"received_at": "header:Date", "sender": "header:From", "subject": "header:Subject",
               "body_offset_in_file": 122, "order_numbers": ["body:char:99-104"],
               "claims": {"stay_block": "body:char:56-59", "pod_block": "body:char:88-91"}}
}
```

Rules:
- **Nothing is masked in A's records.** `sender`, `to`, `body` and the claimed blocks are personal data. B/C/D
  must mask them before the AI model or a customer sees them. `pii_detected` counts what
  `backend/unstructured/masking.py` would hide (email, NRIC, phone, unit, postal, block); B/C/D may reuse it.
  Names in free text are not detected by rule.
- `system_hint` is set only when the email itself writes `V1-`/`V2-`. Choosing v1 or v2 is B's candidate lookup
  (T-A01). A passes the number + `received_at` so B can rule out orders created after the email (T-A02/T-A03).
- `body:char:<a>-<b>` indexes into `body` (the text after the blank line, line endings as `\n`);
  `body_offset_in_file` gives the body's start in the file.
- `status`: `ok` · `partial` (no order number in a complaint, unknown category, bad date, several numbers) ·
  `failed` (not UTF-8, missing headers, empty). Every file gets a record and a `manifest.json` entry.

Policy chunks (`policy_chunks.jsonl`). **Guide received 16 Nov** as the "Resolution Guide" tab of
`CS_case_log_Oct25-Jun26.xlsx` (client Q01/Q02; copy it into `<package>/tabular/`, git-ignored). One chunk per rule row
(9) and per note (3). Synthetic sample:

```json
{"source_id": "policy:CS_case_log_Oct25-Jun26:resolution_guide", "type": "document",
 "ref": "data/tabular/CS_case_log_Oct25-Jun26.xlsx", "locator": "sheet:Resolution Guide|row:5",
 "heading": "Late delivery", "text": "Complaint type: Late delivery. Check first: …. Resolution: …. Limit / approval: …",
 "fields": {"Complaint type": "…", "Check first": "…", "Resolution": "…", "Limit / approval": "…"},
 "email_categories": ["late"], "guide_version": "v2", "guide_updated": "2026-03-02",
 "authority": "Client Q02 (16 Nov 2026): one guide version in use; apply it to every case whatever the complaint date"}
```

Email category → guide rule: `late` → Late delivery · `where_is_parcel` → Parcel not received · `thrown_over_gate`
→ Damaged / thrown parcel · `wrong_address` → Wrong address · `cod_wrong` → COD overcharge · `missing_item` → Item
missing · `corporate` (any MERL-C-* account) → Corporate account. `compliment` has no rule. The "Case Log" tab is
B's and is not read by A. `.xlsx` (guide tab), `.md`/`.txt`/`.csv` are parsed; other formats → `UNSUPPORTED_FORMAT`.

### 5. A's tool results (common envelope from the team plan)

`search_policy(query="", effective_date=None, *, category=None)` and `search_emails(query, order_number=None)`
return the envelope below. `category` (added 17 Nov, optional) returns that complaint type's guide row directly;
`effective_date` does not filter because the client applies guide v2 to every case (Q02) — each hit carries
`authority`, `guide_version` and `fields`.

```json
{"ok": true, "status": "found", "data": [{"text": "…snippet (unmasked; C masks)…", "score": 0.82, "citation": {"…": "…"}}], "sources": ["email:2026-01-01_000"], "error": null}
```

| `status` | Meaning for A's tools |
|---|---|
| `found` | at least one cited result |
| `not_found` | searched successfully, nothing relevant |
| `partial` | results returned, but some sources failed or are low-confidence |
| `failed` | the dependency failed (index missing, endpoint down). `error: {code, message, retryable}` |

`search_policy` returns `failed` with `error.code = "SOURCE_MISSING"` only if the guide workbook is not in
`<package>/tabular/` (T-A18); a category with no rule (e.g. `compliment`) returns `not_found` — never an invented rule.
`INDEX_MISSING` means the ingest has not been run. `ok` is `false` only for `failed`.

**Updated 17 Nov (team decision): hybrid retrieval.** Both tools take `mode="hybrid"` (default) | `"vector"` |
`"keyword"`; every result carries `retrieval` (`hybrid:keyword+<embed model>`, `vector:<model>`, `keyword`,
`keyword (fallback: <CODE>)`, `category`, `order_filter`, `all_rules`). Vector side = embeddings of masked text in
FAISS, chunks + citations in SQLite (`vector_index.py`, handoff `Ralph_2026-11-17-vector-index.md`). Embedding model
today: `local-tfidf-chargram-v1` (numpy, offline; the API key has no credit); `text-embedding-3-small` via
`A_EMBED_MODEL` when credit returns. If it is
unavailable (`NO_FAISS`, `INDEX_MISSING`, `INDEX_STALE`, `EMBED_<HTTP code>`), hybrid falls back to keyword and says
so; `mode="vector"` returns `failed` with that code. Hit shapes and citations below are the same in every mode.

Code: `backend/unstructured/search.py`. Each `search_emails` hit:
`{text, score, category, is_complaint, received_at, order_numbers, citation}` where `citation.locator` =
`body:char:<a>-<b>` and `body[a:b] == text` exactly. Each `search_policy` hit: `{text, score, heading, fields,
guide_version, authority, citation}`. Why keyword search and not embeddings, with measurements:
`docs/03-Handoffs/Ralph_2026-11-17-guide-and-client-answers.md`.

### 6. A's telemetry lines (draft until C's shared telemetry contract)

One JSON line per call in `output/unstructured/telemetry.jsonl`. Never prompt, query, image or answer text.

```json
{"ts": "2026-11-18T02:00:00+00:00", "tool": "pod_extract|ratecard_extract", "source_id": "pod:v1:99999", "model": "gpt-4o-mini",
 "prompt_version": "pod-v1", "status": "ok|failed", "error": null, "cache": "hit|miss", "attempts": 1, "latency_ms": 2100,
 "prompt_tokens": 0, "completion_tokens": 0}
{"ts": "…", "tool": "search_emails|search_policy", "status": "found", "hits": 3, "latency_ms": 4}
```

### Open points for B/C on 17 Nov

1. B: one `orders` key `(source_system, order_id)`. Does B want POD records keyed the same way? (proposed: yes)
2. B: who owns COD truth when the card and `cod_amount` differ (T-A08)? Proposed: store both, the app shows both.
3. C: is `locator` precise enough for the final-answer citation check?
4. ~~All: where does masking happen?~~ **Decided 16 Nov (John): not in A. A returns everything unmasked; B/C/D
   mask.** Still open for C: mask before the AI model sees the text, or only on the final answer? (PDPA question
   likely at the demo.)
