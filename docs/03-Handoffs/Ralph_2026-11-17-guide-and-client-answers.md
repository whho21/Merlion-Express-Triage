# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-17 (SGT)
**Topic**: Resolution Guide ingestion, client answers Q03/Q04/Q06/Q07/Q08 applied, retrieval choice

## Scope

- **Resolution Guide (client Q01/Q02).** The client sent `CS_case_log_Oct25-Jun26.xlsx` (16 Nov 8:00 PM). Copy it
  into `<package>/tabular/` (git-ignored; it has customer names and phone numbers). `python -m backend.unstructured.ingest`
  now reads its "Resolution Guide" tab (standard-library `.xlsx` reader, no new dependency): v2, updated 2 Mar 2026,
  **9 rules + 3 notes**, each cited `sheet:Resolution Guide|row:<n>`. The "Case Log" tab is B's and is not read.
- **`search_policy(query="", effective_date=None, *, category=None)`** — `category` is an email category (or
  `corporate`) and returns that complaint type's rule row directly. Every hit carries `authority` (Q02: guide v2
  applies to every case whatever its date), `guide_version` and the rule's `fields`.
- **Rates (`ratecard.lookup_rate`)**: Q06 April card applies retrospectively to every order (flagged and cited); Q07
  upper limit inclusive (3 → ≤3, 10 → 3–10, 25 → 10–25, >25 not on card); Q08 standard delivery only; Q03 ops zones
  map to price rows. The extracted card itself is unchanged (no new paid run; rebuilt from cache, US$0).
- **POD (`pod.find_pod`)**: any v2 order → "No POD on file … (client Q04)", worded so it never implies a check.
- **Package folder**: default data folder is `data/team2_merlion_express_package/` if present (plan v0.5), else
  `data/`; `--data` overrides. Source refs are repo-relative.
- **Evals**: `evals/developer_a_cases.json` now **18 cases, 18/18 pass** on the real package. Two old expectations
  were wrong after the client's answers and are replaced (missing guide → guide rule cited; 10 kg "ambiguous" →
  3–10 kg band); added retrospective rate, exact 3 kg, over 25 kg, corporate escalation, plain-words relevance,
  no-rule-for-compliment and ops-zone cases. Unit tests: **70 pass** (synthetic data, no network).

## Retrieval choice: keyword search, not embeddings (plan v0.5 asks A to document and evaluate this)

| Corpus | Size | Why keyword search fits |
|---|---|---|
| Resolution Guide | 9 rule rows + 3 notes | Each email is already classified into the guide's complaint types, so the main path is an exact category lookup, not similarity |
| Complaint emails | 90 short template emails | Lookups are by order number (exact) or by obvious words; citations must point at exact characters |

Measured 17 Nov on the real guide (top-1 = the right rule ranked first):

| Check | Result |
|---|---|
| Category lookup, 7 email categories + `compliment` | **7/7 exact; compliment → `not_found`** |
| 12 plain-language questions, before synonyms | 10/12 (missed "wrong **block**" and "extra **cash on delivery**") |
| Same 12 after a 15-word query-side synonym list (`search.QUERY_SYNONYMS`) | 12/12 (tuned on these, so optimistic) |
| 4 fresh questions not used for tuning | 3/4 (the miss — "item inside was smashed" — ranks the right rule 2nd) |

Embeddings would cost API calls and a vector index for 12 short rows, and add a second source of error to
citations, for at most the one hold-out miss above. Revisit if Jeffrey's realistic questions show misses the
category path can't cover; FAISS + the class embedding endpoint remain the fallback (plan v0.5).

## Remaining

- Jeffrey's realistic customer questions → re-measure the table above (task 4).
- Agree contracts §2–§6 with B/C (task 3); hand A's files to B/C by the agreed private route, not Git (task 5).
- For B: 73 of 79 complaint senders appear in the case log "Contact" column with an "Order Ref"
  (formats `12345`, `#12345`, `V1-12345`, `v1 12345`, `ORD12345`) — useful for v1/v2 identity (T-A01).
- CBD-ERP surcharge (CBD postal districts + 07:30–19:00) and public-holiday checks (SG calendar) are not applied in
  `lookup_rate`; whoever composes the quote adds them (Q08). E maintains calendar lookup files per plan v0.5.

## Next Step

- B: copy the workbook into `<package>/tabular/`; use `lookup_rate` for `get_rate` with the ops zone from the address.
- C: call `search_policy(category=<email category>)` for the rule; show `authority`; mask before the model.
- E: run `python -m backend.unstructured.evals` (18 cases) or fold `evals/developer_a_cases.json` into the runner.
