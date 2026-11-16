# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-16 (SGT)
**Topic**: Task 4 — complaint-email and policy/guide parsing

## Scope

- `backend/unstructured/` — email parser, policy/guide parser and an ingest command with a per-file manifest.
  Standard library only; no LLM calls, no API spend.
- **Records are unmasked** (team decision, John, 16 Nov: A extracts everything, B/C/D mask). `masking.py` stays as
  a shared helper B/C/D can reuse; A only uses it to count personal data (`pii_detected`).
- Run on the real package (16 Nov): **90/90 emails parsed `ok`, 0 partial, 0 failed.** Categories: wrong address 17 ·
  item missing 16 · where is my parcel 16 · COD wrong 14 · late 11 · compliment 8 · thrown over gate 8 (same as the
  audit). 82 emails carry one order number; none has a V1/V2 prefix; 11 corporate. Personal data detected: 16
  phone numbers, 34 block numbers, plus the sender address on all 90.
- Checks: 28 unit tests pass (synthetic data only). On the real output: body and sender equal the source file in
  90/90; every order-number locator points at the right text (0 mismatches); order numbers equal the audit
  script's extraction for all 90 files.
- Policy: `SOURCE_MISSING` recorded in the manifest (no `tabular/` folder, client question A-Q1).
- `contracts.md` section 4 updated to the record the code really produces.

## Remaining

- `.pdf` / `.xlsx` / `.docx` guide formats are not parsed yet (visible `UNSUPPORTED_FORMAT`). Add one when the guide
  arrives and we know its format.
- Masking now sits with B/C/D. Names inside free text are not caught by `masking.py` rules (none seen in the
  90 emails, but POD `received_by` has names), so the guardrail must check names too.
- ~~`search_emails` / `search_policy` (task 7) and POD / rate-card extraction (task 5) not started.~~ Built later
  on 16 Nov — see `Ralph_2026-11-16-A-tools-evidence-limits.md`.

## Next Step

- B: confirm you want `order_numbers` + `received_at` as the input to candidate lookup (contracts open point 1).
- C: decide whether you mask before the AI model sees email text or only on the final answer (contracts open
  point 4). `masking.py` is ready to reuse.
- A: task 5 — POD and rate-card extraction with the class vision endpoint, validated against SQL; due Mon 23 Nov 09:00.
