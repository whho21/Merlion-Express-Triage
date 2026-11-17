# Handoff

- **Date-Timestamp**: 2026-11-18 00:20 (SGT)
- **From**: John Phang (C)
- **To**: 
    - Ho Wai Hong (E — shared eval runner)
    - Jeffrey Kong (D — journey cases, separate file)
- **Topic**: HTTP-01–03 eval case pack (26 cases) with executable expectations schema

## Scope

- Added `evals/complaint_api_http_cases.json`: **26 contributed cases** for HTTP-01/02/03 in an extended, runner-executable schema — **19 run on the synthetic fixture provider alone, 7 need live seeded MySQL + A's local evidence** (`requires: "sql"`).
- Schema per case: `id`, `owner`, `category`, `requires`, `client_rule` (the client answer / catalog rule each case guards), and ordered `steps` (`complaint | message | recover | restart`) with executable `expect` assertions: HTTP code, body `status`, `error_code`, `guardrail`, candidate/citation counts, per-evidence-card statuses, `recommendation_null`, clarification, `follow_up_contains`, `text_absent` (privacy/leak guards), `provider_calls_delta`, and `messages_withheld`.
- Coverage this pack adds: **4 deterministic refusals** (override, NRIC verification, self-approval, follow-up refusal — gate needs ≥2) and **5 kill-shot phrasings** (override, NRIC, self-approval, claimed-refund amount, "confirm it was stolen in writing"). C's task-8 quota (eight cases, ≥2 refusals, five kill-shots) is met by this pack plus the existing five-case starter.
- All refusal regexes, order-reference hints and the POD-absence identity (V2-20001 is absent from A's 80-record set) were verified against the current source before writing; expected statuses match implemented behaviour, not aspirations.
- The sql cases were executed manually on 17 Nov against the seeded database; statuses quoted are observed results.

## Remaining

- **Runner support (E):** `restart` step action (kill/relaunch the API against the same session DB), `$session_id`/`$first` step-target references, and `provider_calls_delta` counting via the fixture provider's call counter. The synthetic-only 19 should run without MySQL; the sql 7 need `scripts.check_sql_provider` to pass first.
- **Assertions beyond the schema:** two notes ask for exact-string checks (POD-absence wording per client Q04; evidence-list length at selection). Worth promoting into the schema later rather than special-casing.
- **Not converted to runner cases** (already covered by unit tests and awkward to automate at HTTP level): future-created exclusion, mixed date precision, source-changed between turns (`409 SOURCE_CHANGED`), concurrent-turn compare-and-swap, timeout capacity. These stay in `backend/api_service/tests/` — the runner should not duplicate them.
- The existing five-case starter (`evals/complaint_api_cases.json`) stays as E's first-increment target; this pack is the extension, not a replacement.

## Next Step
| S/N | Name | Task |
| --: | --- | --- |
| 1 | Ho Wai Hong (E) | Wire the 19 synthetic cases into the shared runner with the step/expect schema (restart action included); report first results by 18–19 Nov per your task 3 |
| 2 | Ho Wai Hong (E) | Gate the 7 sql cases behind a `check_sql_provider` preflight; mark them skipped (not failed) when MySQL is unavailable |
| 3 | Jeffrey Kong (D) | Keep your three journey cases in `evals/developer_d_cases.json` separate; cross-reference any overlap with this pack at the next sync |
| 4 | John Phang (C) | Review the first runner increment results; flip case C-HTTP02-03's expectation in the same commit if message+selection interpretation is implemented |
