# PR #11 review — guide and client rules

**Reviewed:** 17 Nov 2026, SGT. **PR:** [#11](https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express/pull/11). **Head:** `3bd8d51bcf8cfd3e9aa6334523bfc498fc7298f4`.

Scope: changed extraction/retrieval code, client answers, file-backed integration and relevant tests. Review performed in an isolated temporary checkout; no implementation changes, branch switches, paid model calls or GitHub comments/reviews were made. This report is the only new workspace artifact from the review.

## Findings

### [P2] Preserve a valid category match when query ranking finds no words

**Location:** `backend/unstructured/search.py:153–164`, particularly lines 157–158.

The new public contract says category lookup returns that complaint type's guide row directly. However, when both `category` and `query` are supplied, keyword ranking can remove the correctly matched row: `search_policy(category="late", query="Please help with order 20001")` returns `not_found`, while the same call without query returns the Late delivery rule.

This can cause C to report missing policy for an already-classified complaint. Return the exact category rule independently of lexical overlap, or retain category matches as a fallback when ranking produces no hits; add a test supplying both arguments with no matching words. Evidence: current `search_policy` docstring, category-to-guide metadata and the stated category-first retrieval design in Ralph's handoff.

### [P2] Restrict retrospective fallback to dates before the authorised card

**Location:** `backend/unstructured/ratecard.py:169–175`.

Fallback runs whenever no active card matches, including when the April card has expired. With a synthetic April card whose `effective_to` is `2026-04-30`, a query for `2026-05-01` returns `found` and `applied_retrospectively: true`, ignoring the explicit end date.

Client Q06 authorises the April card for earlier orders in the supplied package; it does not authorise using an expired card after its validity ends. Require the requested day to precede the authorised card's start (and respect the authorised data scope); otherwise return no applicable card. Add an expired-card regression alongside the existing pre-April test. Source: `docs/00-Biz_Requirements/client_qa_v02.xlsx`, Client Q&A sheet, Q06 response (`E7`). The supplied current card has no end date, so this is an uncovered validity edge relevant to subsequent batches, not a claim that current card prices are wrong.

### Follow-up — remove the fixed date from POD messaging

**Location:** `backend/unstructured/pod.py:196–207` (`find_pod`).

Keep lookup based on available system/order records and replace the hard-coded migration-date explanation with **“No POD on file for this order in the supplied dataset.”** If a coverage date is useful, derive the latest validated POD date from the relevant records and cite it as the latest available observation, not proof of complete coverage or a cutoff that excludes later scans.

Add checks for an empty dataset and a later batch containing a matching v2 POD; the latter must be returned normally without changing a date constant.

## Verification and coverage

| Requirement / behaviour | Verification | Result |
|---|---|---|
| Existing and added synthetic code checks | `python3 -B -m unittest discover -s backend/unstructured/tests -v` in isolated PR checkout | 70 tests passed |
| Native Excel guide and existing emails | `ingest.run()` using actual local sources, with workbook exposed under temporary `tabular/` as documented | 90 emails; 12 guide chunks (9 rules + 3 notes) |
| Category-first policy lookup | Synthetic guide; exact category with/without unrelated query text | Finding reproduced: found without query; not_found with query |
| Card expiry versus retrospective authority | Synthetic normalised April card, explicit April end date, May request | Finding reproduced: expired card returned as found |
| POD coverage messaging | Source inspection of `find_pod` | Fixed date occurs in the missing-v2 explanation; follow-up requested, new batch tests pending |
| Developer A eval file | `evals.run_cases()` against fresh text ingestion and any available local extraction outputs | 9 PASS; 9 PENDING; no FAIL |
| Paid image extraction | Not executed; no POD/rate/image-manifest output files available in this checkout | Cannot independently verify the PR's full 18/18 real-data result |

Current hybrid design remains compatible: no SQL migrations were introduced, guide/rate/POD/email tools remain file-backed, and backend orchestration can consume the existing envelopes/citations. The workbook must be placed under the selected package's `tabular/` per the PR's instructions; a workbook left at `data/CS_case_log_Oct25-Jun26.xlsx` is not auto-discovered from the nested default package root.

## Fix handoff

Ralph: address the two findings and POD messaging follow-up at the next code push, with focused regression tests. Rerun the unit suite and 18 evals with cached extraction outputs, recording PASS/FAIL/PENDING explicitly; C reviews the changes and E incorporates the checks without treating pending cases as passed.

No SQL migration or new paid extraction is needed for these fixes.
