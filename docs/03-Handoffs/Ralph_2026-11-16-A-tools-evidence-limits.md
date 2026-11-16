# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-16 (SGT)
**Topic**: A tasks 5–9 — image extraction, cache, tools for B/C, eval cases, evidence and limits

## Scope

What B, C and D can use now (all in `backend/unstructured/`, standard library only; how to run: its `README.md`):

| For | What | Status |
|---|---|---|
| B | `pod_records.jsonl` — one record per POD card, validated against SQL (contracts §2) | Code done, 60 unit tests pass. **Real run waits for the team key** |
| B | `rate_cards.jsonl` + `ratecard.lookup_rate()` for `get_rate` (contracts §3) | Same |
| B | `pod.find_pod()` for `get_pod` — `not_found` for any v2 order | Done |
| C | `search_emails(query, order_number=None)` — exact `body:char` citations (contracts §5) | **Working on the real 90 emails** |
| C | `search_policy(query, effective_date=None)` — `failed / SOURCE_MISSING` until the guide arrives | Working |
| C | Telemetry lines per call: tokens, latency, cache hit/miss, no content (contracts §6) | Draft until C's contract |
| D | `evals/developer_a_cases.json` — 12 cases; `python -m backend.unstructured.evals` | 6 pass, 6 pending the image run |

Checks run 16 Nov: 60 unit tests pass (synthetic data, fake model, no network). Real data: ingest 90/90 emails ok;
SQL reference loads 25,833 orders and 24,802 deliveries (same as B's MySQL load); dry run = 80 POD cards + 1 rate
card to send, 0 cached; a card read by eye (`POD_v1_24377`, with the "I8" look-alike) goes through validation with
every key field matching SQL and the look-alike flagged.

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

## Remaining

- Paid image run (needs the team key in the team repo `.env`): `--limit 2` first, then all; then the 6 pending evals.
- Task 5's "one image-derived cited answer" demo — after the run (e.g. `find_pod("v1", 24377)` with its citation).
- Agree contracts §2–§6 with B/C at the 17 Nov sync (task 3); fold A's eval cases into D's runner.
- Refresh the evidence table with the real extraction numbers after the run.

## Next Step

- Ralph: put the team key into the team repo `.env` (never commit it), then run the smoke test.
- B: load `pod_records.jsonl` / `rate_cards.jsonl` keyed by `(source_system, order_id)`; use `lookup_rate` for `get_rate`.
- C: call `search_emails` / `search_policy`; mask before the model sees the text.
