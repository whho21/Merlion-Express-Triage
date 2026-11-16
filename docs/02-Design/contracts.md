# Contracts (Technical)

- Freeze minimum contracts by 17 Nov. Use typed models or JSON Schema, sample success/failure responses and synthetic fixtures; record changes
- C coordinates; all agree

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
- Other flags: `remark_contradicts_signature`, `remark_contradicts_receiver` (T-A09), `model_unreadable:<key>`,
  `order_ref_differs_from_file_name`.
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
  "bands": [{"band": "<=3kg", "min_kg": 0.0, "max_kg": 3.0, "boundary_rule": "UNRESOLVED (client A-Q4)"}],
  "rows": [{"zone": "Central", "band": "<=3kg", "min_kg": 0.0, "max_kg": 3.0, "boundary_rule": "UNRESOLVED (client A-Q4)",
            "price": 0.00, "locator": "row:Central/col:<=3kg"}],
  "surcharges": [{"name": "same_day", "zone": "Central", "amount": 0.00, "available": true, "raw": "+$0.00"},
                 {"name": "CBD ERP hours (0730-1900)", "band": "<=3kg", "amount": 0.00}],
  "notes": {"raw": ["…every line under the table…"], "cod_handling": {"pct": 0.0, "min": 0.0},
            "reattempt_fee": {"amount": 0.0, "from_attempt": 3}, "gst_included": false, "gst_pct": 9.0,
            "corporate_rebate": {"pct": 0.0, "above_parcels_per_month": 0}, "public_holiday_rule": "…"},
  "status": "ok", "issues": [], "extraction": {"…": "as POD"}
}
```

`ratecard.lookup_rate(cards, zone=, weight_kg=, on_date=)` (for B's `get_rate`) returns the tool envelope:
- `not_found` for a date before the earliest `effective_from`, with the reason. Never falls back to the April card (T-A15).
- `ambiguous` when the weight sits on a shared band edge (3 kg, 10 kg); `data` holds both candidates (T-A16).
- `found` with `{price, band, citation}`; the citation locator is `row:<zone>/col:<band>`.
- Zone and service type are inputs: the orders table has neither (client question A-Q4).

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

Policy chunks (`policy_chunks.jsonl`, empty until the Resolution Guide arrives):
`{"source_id": "policy:<stem>", "type": "document", "ref": "data/tabular/<file>", "locator": "section:<heading>|line:<a>-<b>" or "row:<n>", "heading": "…", "text": "…"}`.
`.md`/`.txt`/`.csv` are parsed; other formats get a visible `UNSUPPORTED_FORMAT` outcome.

### 5. A's tool results (common envelope from the team plan)

`search_policy(query, effective_date=None)` and `search_emails(query, order_number=None)` return:

```json
{"ok": true, "status": "found", "data": [{"text": "…snippet (unmasked; C masks)…", "score": 0.82, "citation": {"…": "…"}}], "sources": ["email:2026-01-01_000"], "error": null}
```

| `status` | Meaning for A's tools |
|---|---|
| `found` | at least one cited result |
| `not_found` | searched successfully, nothing relevant |
| `partial` | results returned, but some sources failed or are low-confidence |
| `failed` | the dependency failed (index missing, endpoint down). `error: {code, message, retryable}` |

`search_policy` returns `failed` with `error.code = "SOURCE_MISSING"` until the Resolution Guide arrives (T-A18).
`INDEX_MISSING` means the ingest has not been run. `ok` is `false` only for `failed`.

Code: `backend/unstructured/search.py`. Keyword ranking, no embeddings (no spend). Each `search_emails` hit:
`{text, score, category, is_complaint, received_at, order_numbers, citation}` where `citation.locator` =
`body:char:<a>-<b>` and `body[a:b] == text` exactly. Each `search_policy` hit: `{text, score, heading, citation}`.

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
