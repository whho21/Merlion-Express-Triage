# Complaint emails — observations (Developer A, 17 Nov 2026)

Sanitised: counts, wordings with numbers removed, and order numbers only. The per-email spreadsheets
(`complaints_overview.csv`, `complaints_vs_pod.csv`) hold customer details and stay in `output/unstructured/`
(git-ignored); ask Ralph for them by a private route.

## 1. Only 7 wordings

The 90 emails are 7 fixed sentences with the numbers changed. Example (17 emails, identical apart from the numbers):

> You delivered my parcel to the wrong block!! I stay blk N but the POD photo shows blk N. Order N. Please retrieve ASAP.

| # | Wording | Count | Tone |
|---|---|---:|---|
| 1 | Wrong address delivered (above) | 17 | angry ("!!") |
| 2 | Box arrived opened, one item missing… Driver say not his problem | 16 | disappointed |
| 3 | I ordered N days ago and tracking still say IN_TRANSIT… This is ridiculous | 16 | angry |
| 4 | Driver collect $N extra for COD… Please refund the difference | 14 | neutral |
| 5 | This is the Nrd late delivery this month… (corporate MERL-C-N)… switch to your competitor | 11 | threat to leave |
| 6 | Just want to say your driver DRVN very polite and helpful… | 8 | **compliment** |
| 7 | Your driver just THREW my parcel over the gate. Got video somemore. Item inside broken | 8 | angry, Singlish |

No profanity in any email.

**What it means:** classification by wording is exact and free (no LLM). But the judges will type complaints in their
own words at the demo, so `search_policy` / `search_emails` use keyword search plus everyday-word synonyms, measured
in `docs/03-Handoffs/Ralph_2026-11-17-guide-and-client-answers.md`.

## 2. 8 of 90 are compliments, not complaints

Wording 6 names a driver code and no order number. They must stay out of complaint counts and the weekly
driver/zone view (trap T-A04); `emails.jsonl` marks them `is_complaint: false`.

## 3. Almost no proof of delivery to tally against

- 82 complaints quote an order number. **Only 1 (`22574`) has a POD scan**, dated 29 Oct 2025 — 8 months before the
  complaint, so almost certainly the old system's order with the same number (T-A06).
- The other 81 have no scan. Client Q04 (16 Nov): no POD exists for any order after 1 Feb 2026. The app must say
  "no POD on file" plainly and never imply a check.
- 17 emails quote "the POD photo shows blk N" — for a photo we do not have.

## 4. Customer claims do not match the records

| Claim | Checked against | Result |
|---|---|---|
| "I stay blk N" (17 wrong-address emails) | `orders.delivery_address` for v1 and v2 | matches **0 / 17** |
| "still IN_TRANSIT" (16 where-is-my-parcel emails) | `orders.status` | database says DELIVERED **16 / 16** |
| Total complaints that contradict POD or database | | **33 of 82** |

**What it means for the app:** quote the data, state that the customer's claim differs, never repeat the claim as
fact (hallucination deduction). Good demo material; `complaints_vs_pod.csv` has one row per complaint with the reason.
