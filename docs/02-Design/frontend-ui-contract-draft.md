# Frontend consumer contract — DRAFT (D → C)

**Proposed by:** Jeffrey (D). **Reviewer:** John (C); Jenn (B) for the weekly section. **Status:** proposal for the 17 Nov sync, not frozen.
**Date:** 17 Nov 2026 (SGT).

`contracts_2026-11-16.md` says route paths and JSON schemas are C's decision. This file records **what the React UI currently expects**, so C can confirm, rename or reject fields. If C changes a name, only `frontend/src/api/client.js` (and the mock fixtures) need editing.

All examples are synthetic.

## 1. Routes the UI calls (proposed)

| Purpose | Method + path | Body / query |
|---|---|---|
| Triage a complaint | `POST /api/complaints` | `{ "email_text": "...", "session_id": null }` |
| Follow-up / clarification | `POST /api/sessions/{session_id}/messages` | `{ "message": "...", "selected_candidate": {"system_version": "v1", "order_id": 97042} }` (either field) |
| Recover session after restart | `GET /api/sessions/{session_id}` | — |
| Weekly view | `GET /api/weekly?week_start=YYYY-MM-DD` | — |
| List available weeks | `GET /api/weekly/weeks` | — |
| Health | `GET /api/health` | — |

Errors: any non-2xx with body `{ "error": { "code": "DEPENDENCY_UNAVAILABLE", "message": "...", "retryable": true } }`. The UI shows **Retry** only when `retryable` is true.

## 2. Complaint / session response

```json
{
  "request_id": "req-…",
  "session_id": "sess-…",
  "status": "found | ambiguous | partial | not_found | refused | failed",
  "complaint": { "category": "Late delivery", "claims": ["…"], "citations": [1] },
  "order": { "system_version": "v2", "order_id": 98101, "customer": "Mr T*** (masked)", "postal_code": "5****0",
             "zone": "North-East", "driver_code": "DRV107", "promised_date": "2026-03-09", "citations": [2] },
  "candidates": [ { "system_version": "v1", "order_id": 97042, "created": "2026-01-21", "status": "DELIVERED",
                    "zone": "West", "postal_code": "6****8", "evidence_for": "…", "citations": [2] } ],
  "clarification": { "question": "…", "hint": "…" },
  "evidence": [ { "key": "delivery | pod | gps | rate | policy", "title": "…", "status": "found | not_found | partial | failed",
                  "summary": "…", "facts": [["Label", "Value"]], "citations": [3],
                  "gps": [{ "t": "15:40", "dist": 42 }], "deliveredAt": "15:42", "note": "…" } ],
  "conflicts": [ { "field": "Amount collected", "values": [{ "value": "S$22.00", "source": "POD card remark", "citation": 3 }], "note": "…" } ],
  "recommendation": { "action": "Refund | Re-deliver | Reject | Apology only | Compensate", "amount_sgd": 7.09,
                      "summary": "…", "rationale": "…", "approval_required": false, "approver": "Agent | Head of CX (PN)",
                      "citations": [6] },
  "abstention": { "reason": "…" },
  "guardrail": { "code": "POLICY_OVERRIDE_ATTEMPT", "pii_masked": ["NRIC"] },
  "follow_up_answer": "…",
  "limitations": ["…"],
  "citations": [ { "n": 1, "source_id": "email:…", "type": "document | sql | image | tabular | log",
                   "ref": "…path or table…", "locator": "body:char:12-96", "record_key": { "system_version": "v2", "order_id": 98101 },
                   "label": "Customer email" } ],
  "recovered": false
}
```

Rules the UI relies on:

1. `citations[].n` is a display number; every `citations: [n]` elsewhere must point to an entry in the list. The citation fields (`source_id`, `type`, `ref`, `locator`, `record_key`) follow Ralph's A contract §1.
2. `status` drives the banner: `refused` = guardrail refusal (deterministic); `not_found` = honest abstention; `failed` = dependency failure. HTTP 200 with `failed` is allowed and shows the error banner.
3. `recommendation` is `null` unless policy supports it. `abstention.reason` is shown instead.
4. Text fields arrive **already masked** (decision 16 Nov: B/C/D mask; the UI does not unmask or re-mask).
5. `evidence[].status = not_found` for POD after 1 Feb 2026 must say nothing was checked (client Q04).
6. Generic `system_version`/`order_id` names are used as-is (no `source_system` alias in the UI).

## 3. Weekly response (B computes, C exposes)

```json
{
  "period": { "week_start": "2026-02-16", "week_end": "2026-02-22", "timezone": "Asia/Singapore" },
  "definitions": [["Week", "…"], ["Complaint", "…"], ["Zone", "…"], ["Unknown", "…"]],
  "totals": { "rows_logged": 27, "complaints": 25, "duplicates_merged": 2, "compliments_excluded": 0,
              "unknown_zone": 4, "unknown_driver": 2, "refunds_sgd": 268.18, "vouchers_sgd": 130.0,
              "approvals_needed": 3, "approvals_missing": 0, "guide_gaps": 5 },
  "by_zone": [{ "zone": "North", "complaints": 6 }],
  "by_driver": [{ "driver_code": "DRV109", "complaints": 3, "main_zone": "Central", "top_category": "COD overcharge" }],
  "by_category": [{ "category": "Late delivery", "complaints": 7 }],
  "by_resolution": [{ "resolution": "Refund", "cases": 5 }],
  "zone_category": { "zones": ["North", "…", "Unknown"], "categories": ["Late delivery", "…"], "rows": [{ "zone": "North", "values": [1, 0, 2] }] },
  "trend": [{ "week_start": "2025-12-01", "total": 14, "by_zone": { "North": 3, "Unknown": 1 } }],
  "limitations": ["…"],
  "citations": [{ "n": 1, "source_id": "tabular:case_log", "type": "tabular", "ref": "…", "locator": "…", "label": "CS case log" }]
}
```

Zones are the five ops zones (North, North-East, East, Central, West) plus `Unknown` — **not** rate-card price bands (client Q03). `guide_gaps` = cases where the agent's resolution differs from Resolution Guide v2 (client Q02: "the guide is right and I want to see the gap"). B defines exactly how a gap is detected.

## 4. Questions for C / B

1. C: accept these paths, or give yours? Is `status` on the body plus HTTP codes for transport errors acceptable?
2. C: will evidence come back as display-ready `summary` + `facts`, or raw tool output the UI must format? (UI prefers display-ready, validated server-side.)
3. C: session IDs — returned on first response and kept in the browser (`localStorage`) for restart recovery. OK?
4. B: confirm weekly definitions (week boundary SGT Mon–Sun by date opened; duplicate rule; compliments excluded; zone from address).
5. B: which `guide_gaps` checks are feasible by 23–24 Nov (e.g. refund > $50 without PN approval; refunded claimed COD figure)?
