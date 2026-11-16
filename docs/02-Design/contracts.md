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

```json
{
  "source_id": "pod:v1:99999",
  "image_ref": "data/images/proof_of_delivery/POD_v1_99999.jpg",
  "image_sha256": "…",
  "source_system": "v1",
  "order_id": 99999,
  "fields": {
    "order_ref":      {"value": "V1-99999",         "confidence": "high"},
    "delivered_at":   {"value": "2025-10-02T16:16", "raw": "02/10/2025 16:16", "tz": "Asia/Singapore (assumed)", "confidence": "high"},
    "driver_code":    {"value": "DRV000",           "confidence": "high"},
    "postal_code":    {"value": "000000",           "confidence": "high"},
    "received_by":    {"value": "A. Tan (synthetic)", "kind": "name|role|blank", "role": null, "confidence": "medium"},
    "signature":      {"value": "present",          "confidence": "high"},
    "remarks":        {"value": "COD collected $10","confidence": "high"},
    "cod_on_card":    {"value": 10.00, "currency": "SGD", "confidence": "high"}
  },
  "template": "hotline_footer|thankyou_footer",
  "flags": ["remark_contradicts_signature"],
  "validation": {"matches_sql": {"order": true, "delivered_at": true, "driver": true, "postal_code": true}},
  "extraction": {"method": "vision", "model": "<class endpoint model>", "prompt_version": "pod-v1", "extracted_at": "2026-11-18T10:00:00+08:00", "status": "ok"}
}
```

Rules:
- `raw` keeps the printed text; `value` is normalised (dates day-first, see trap T-A12).
- An unclear character never gets guessed: `confidence: "low"` plus `flags: ["low_confidence:<field>"]`.
- `received_by.value` is stored as read (unmasked; B/C/D mask before showing — John, 16 Nov). `kind` records
  whether it is a name or a role (T-A10). Committed samples stay synthetic.
- `status`: `ok` · `partial` (some fields low confidence) · `failed` (unreadable). Failed records are still emitted.

### 3. Rate card record (A produces → B loads)

```json
{
  "source_id": "ratecard:2026-04-01",
  "image_ref": "data/images/rate_cards/rate_card_apr2026.jpg",
  "effective_from": "2026-04-01",
  "effective_to": null,
  "currency": "SGD", "gst_included": false,
  "rows": [
    {"zone": "Central", "band": "<=3kg",  "min_kg": 0,  "max_kg": 3,  "price": 0.00},
    {"zone": "Central", "band": "3-10kg", "min_kg": 3,  "max_kg": 10, "price": 0.00, "boundary_rule": "UNRESOLVED (client A-Q4)"}
  ],
  "surcharges": [{"name": "same_day", "zone": "Central", "amount": 0.00}, {"name": "cbd_erp_0730_1900", "band": "<=3kg", "amount": 0.00}],
  "notes": ["cod_handling_pct", "reattempt_fee_from_3rd", "public_holiday_rule", "corporate_rebate"]
}
```

Rule: a rate lookup for a date before `effective_from` returns `status: "not_found"` with the reason. It never falls back
to the April card silently (T-A15).

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

### Open points for B/C on 17 Nov

1. B: one `orders` key `(source_system, order_id)`. Does B want POD records keyed the same way? (proposed: yes)
2. B: who owns COD truth when the card and `cod_amount` differ (T-A08)? Proposed: store both, the app shows both.
3. C: is `locator` precise enough for the final-answer citation check?
4. ~~All: where does masking happen?~~ **Decided 16 Nov (John): not in A. A returns everything unmasked; B/C/D
   mask.** Still open for C: mask before the AI model sees the text, or only on the final answer? (PDPA question
   likely at the demo.)
