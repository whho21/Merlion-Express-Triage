# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-16 (SGT)
**Topic**: A tasks 5–9 — image extraction, cache, tools for B/C, eval cases, evidence and limits

## Scope

What B, C and D can use now (all in `backend/unstructured/`, standard library only; how to run: its `README.md`):

| For | What | Status |
|---|---|---|
| B | `pod_records.jsonl` — one record per POD card, validated against SQL (contracts §2) | **Done: 80/80 read, 80/80 key fields match SQL** |
| B | `rate_cards.jsonl` + `ratecard.lookup_rate()` for `get_rate` (contracts §3) | **Done: 12/12 prices match a by-eye reading** |
| B | `pod.find_pod()` for `get_pod` — `not_found` for any v2 order | Done |
| C | `search_emails(query, order_number=None)` — exact `body:char` citations (contracts §5) | **Working on the real 90 emails** |
| C | `search_policy(query, effective_date=None)` — `failed / SOURCE_MISSING` until the guide arrives | Working |
| C | Telemetry lines per call: tokens, latency, cache hit/miss, no content (contracts §6) | Draft until C's contract |
| D | `evals/developer_a_cases.json` — 12 cases; `python -m backend.unstructured.evals` | **12/12 pass** |

Checks run 16 Nov: 63 unit tests pass (synthetic data, fake model, no network). Real data: ingest 90/90 emails ok;
SQL reference loads 25,833 orders and 24,802 deliveries (same as B's MySQL load).

**Image run, 16 Nov (gpt-4o-mini, team key, US$0.32 total — see `docs/04-Testing_Evals/api_spend.md`):**
- POD: 80/80 `ok`; order, delivered time, driver, postal code and block match SQL on **80/80**. Every field read
  with high confidence. Flags: COD conflict with SQL 25 (9 card amounts differ + 16 SQL COD not on the card),
  "left outside" but signed 7, "neighbour" remark vs a role receiver 4, signature reported absent 1 — all equal to
  the by-eye audit except the last (see limitation 7).
- Rate card: effective 2026-04-01, 12/12 prices and all surcharges/notes match a by-eye reading. Status `partial`
  on purpose: the model dropped the "+" on the CBD ERP row; code treats it as a surcharge by its label and flags
  `SURCHARGE_SIGN_MISSING`.

**One image-derived cited answer (task 5):** "When was v1 order 24377 delivered, and by whom?" →
`find_pod("v1", 24377)` = found: delivered 2025-11-18 09:26 by DRV007, cited `pod:v1:24377`
(`data/images/proof_of_delivery/POD_v1_24377.jpg`, `field:delivered_at`, `field:driver_code`), and both values
match SQL `deliveries`. The same question for the v2 order 22574 → `not_found: no POD scan on file`.
A rate example: `lookup_rate(zone="Central", weight_kg=5, on_date="2026-05-01")` → found, cited
`ratecard:2026-04-01` `row:Central/col:3-10kg`; at 10 kg → `ambiguous`; on 2026-01-15 → `not_found`.

Cost control (task 6): answers are cached by image hash + prompt version + model, so a rerun is free; only failed
reads are retried. `--dry-run` shows the count before any spend; `--limit 2` is a cheap smoke test.

## Evidence for answers and the pitch (sanitised: order numbers and file stems only)

| Conflict | Evidence | What the app should say |
|---|---|---|
| Order number fits both systems (T-A01) | 47 of 82 complaint numbers exist in v1 and v2 with plausible dates | "Two orders match; which one?" — B's lookup |
| Number didn't exist yet (T-A02) | `email:2026-03-09_019` cites `32460`; only v2 has it, created after the email | "No order with that number existed on the email date" |
| POD from the wrong system (T-A05/T-A06) | `22574`: complaint `email:2026-06-19_014`; only scan is `pod:v1:22574` from Oct 2025 | "No POD on file for the v2 order"; never reuse the v1 card |
| Customer claim vs data (T-A07) | Claimed blocks match SQL 0/17; "ordered N days ago, in transit" matches 0/16 | Quote the data; say the claim differs |
| COD card vs SQL (T-A08) | 9/9 cards with "COD collected $X" disagree with SQL; e.g. `pod:v1:24002` | Show both values with citations; no refund from one source |
| Rate card date (T-A15) | Only card effective 2026-04-01 | "No rate card on file for that date" |
| Band edge (T-A16) | 3 kg / 10 kg in two bands; 13 + 7 orders sit on an edge | "Ambiguous: boundary rule not given (asked client)" |
| Policy missing (T-A18) | No `tabular/` folder | "Resolution Guide not available; can't recommend by policy" |

## Limitations (say these honestly in the demo)

1. **No Resolution Guide** — no policy-based recommendation until the client answers A-Q1.
2. **POD scans only for v1 Oct–Nov 2025**; every complaint is Mar–Jun 2026, so most complaints have no POD.
3. **One rate card (from 1 Apr 2026)**; no zone or service type in `orders` — rates need the client's mapping (A-Q2, A-Q4).
4. **Image reading is by the class model**; code validates every key field against SQL and flags look-alikes, but
   fields SQL doesn't hold (receiver, remarks, signature) can't be cross-checked.
5. **Records are unmasked by team decision**; masking (including names, which no rule catches) is B/C/D's.
6. **Email search is keyword-based**; fine for 90 short template emails, weaker for paraphrased questions.
7. **Signature presence is the model's judgement** and SQL can't check it. The run reported one signed card
   (`pod:v1:20659`, a short single stroke) as unsigned; checked by eye, it is signed. Any "absent" is therefore
   flagged `signature_absent_verify_by_eye` and must not be stated as fact.
8. **The model tidies look-alikes itself** (it returned "18/11" for the printed "I8/11" on `24377`), so the
   look-alike flag rarely fires; SQL validation is what catches a wrong key field.

## Remaining

- Agree contracts §2–§6 with B/C at the 17 Nov sync (task 3); fold A's eval cases into D's runner (task 8).
- B/C start using the records and tools (task 7). C's shared telemetry contract replaces §6 if different.

## Next Step

- B: load `pod_records.jsonl` / `rate_cards.jsonl` keyed by `(source_system, order_id)`; use `lookup_rate` for
  `get_rate`. Ask Ralph for the files (they're unmasked and git-ignored — share by hand, never commit).
- C: call `search_emails` / `search_policy`; mask before the model sees the text.
- D: run `python -m backend.unstructured.evals` (12 cases) or fold `evals/developer_a_cases.json` into the runner.
