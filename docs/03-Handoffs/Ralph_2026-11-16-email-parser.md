# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-16 (SGT)
**Topic**: Task 4 — complaint-email and policy/guide parsing

## Scope

- `backend/unstructured/` — email parser, policy/guide parser, PII masking and an ingest command with a per-file
  manifest. Standard library only; no LLM calls, no API spend.
- Run on the real package (16 Nov): **90/90 emails parsed `ok`, 0 partial, 0 failed.** Categories: wrong address 17 ·
  item missing 16 · where is my parcel 16 · COD wrong 14 · late 11 · compliment 8 · thrown over gate 8 (same as the
  audit). 82 emails carry one order number; none has a V1/V2 prefix; 11 corporate. Masked: 16 phone numbers, 34
  block numbers. 0 sender addresses in the output (79 senders → 79 `sender_id`s).
- Checks: 28 unit tests pass (synthetic data only). On the real output: every order-number and claim locator points
  at the right text (0 mismatches); order numbers equal the audit script's extraction for all 90 files.
- Policy: `SOURCE_MISSING` recorded in the manifest (no `tabular/` folder, client question A-Q1).
- `contracts.md` section 4 updated to the record the code really produces (sender hash, issues, locators,
  public view masks claimed blocks).

## Remaining

- `.pdf` / `.xlsx` / `.docx` guide formats are not parsed yet (visible `UNSUPPORTED_FORMAT`). Add one when the guide
  arrives and we know its format.
- Names inside free text are not masked by rule (none seen in the 90 emails). C's output guardrail must still check.
- `search_emails` / `search_policy` (task 7) and POD / rate-card extraction (task 5) not started.

## Next Step

- B: confirm you want `order_numbers` + `received_at` as the input to candidate lookup (contracts open point 1).
- C: confirm masking in A's tools via `public_view()` (contracts open point 4).
- A: task 5 — POD and rate-card extraction with the class vision endpoint, validated against SQL; due Mon 23 Nov 09:00.
