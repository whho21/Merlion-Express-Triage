# Complaint/session API — implementation and consumer handoff

- **Date:** 17 Nov 2026 19:00 (SGT).
- **From:** C / John Phang.
- **To:**
    - Jenn Fang (B — structured provider integration)
    - Jeffrey Kong (D — UI integration)
    - Ho Wai Hong (E — evals runner)
- **Implementation:** HTTP-01 `POST /api/complaints`, HTTP-02 `POST /api/sessions/{session_id}/messages` and HTTP-03 `GET /api/sessions/{session_id}`
- **Status:** local implementation verified; no commit, PR, deployment or consumer acceptance claimed.

## Delivered scope

Ref: Read `docs/02-Design/api-catalog_v0.9.1.md` sections 2–4, 6–8; `frontend-ui-contract-draft.md`; `contracts_2026-11-16.md`.

HTTP-01 `POST /api/complaints`, HTTP-02 `POST /api/sessions/{session_id}/messages` and HTTP-03 `GET /api/sessions/{session_id}` are implemented alongside health. They use typed contracts, fresh request IDs, opaque session IDs, SQLite snapshots, source/candidate checks, safe errors and bounded tool calls. Session recovery survives a real process restart and does not rerun tools.

The API gathers existing cached A POD/policy evidence after a unique or selected identity. Originals are checked against manifest hashes; citations retain logical refs and exact field/guide-row locators. Missing artifacts, failed extraction and no matching record remain different outcomes. Concurrent/incomplete source publication discards observations instead of attaching a new fingerprint to old facts. No ingestion, extraction, SQL writes, model calls or operational actions are performed by these routes.

This is a staged complaint API, not completed live triage. B's production structured lookup is absent; the default provider returns `503 DEPENDENCY_UNAVAILABLE` for an ordinary order request. Requests missing an order reference receive a saved clarification, and prohibited requests receive a deterministic refusal, without that provider. Supported follow-ups return saved POD/policy/GPS evidence summaries. Complete delivery/GPS/rate tools, deterministic policy assessment and answer-model orchestration remain pending. Recommendations therefore remain null. Both weekly endpoints and semantic retrieval remain pending.

## Files and requirements coverage

Source requirements: [implementation plan](John_2026-11-17-complaint-session-api-plan.md), [API catalog](../02-Design/api-catalog_v0.9.1.md) HTTP-01–03 / TOOL-05,08,14 / sections 3,6–8, the frontend contract, and 17 Nov API/mock, guide and PR11 handoffs.

| ID | Implementation | Executed checks / limits |
|---|---|---|
| CS-01 | `backend/api_service/app.py`, `models.py`, `service.py` | HTTP validation, nested response schemas, category projection, clarification, ambiguity, no-match, partial evidence and refusal. `found`/`failed` shapes are defined; complete automated resolution is deferred. |
| CS-02 | `service.order_references`, `validate_source`, message route | Submitted number/system constraints, both explicit systems for the same number, future-created exclusion, offset-aware timestamps, unoffered candidate rejection, source change and no session overwrite. |
| CS-03 | `store.py`, recovery route | Independent sessions, SQLite compare-and-swap conflicts, new app recovery without tool calls; real Uvicorn stop/restart with provider unavailable preserves result, citations and messages. |
| CS-04 | Exception handlers, `BoundedCalls`, health | Generic validation errors without raw fields, 503/504 errors, unavailable health flag, bounded slots that remain occupied after timeout, preserved local CORS and implemented OpenAPI routes. |
| CS-05 | `evidence.py`, `ComplaintResult.references_exist` | Verified source hashes, dangling citation rejection, original changes, interrupted publication, cross-system POD prohibition, later matching v2 accepted, failed extraction retained as failed and exact-category policy lookup. No refund/paid-charge/recipient-identity conclusions are invented. |
| CS-06 | Refusal checks, safe projections, request/tool logs | Refusals before lookup on initial and follow-up requests; safe stored turn markers; personal fields excluded from cached facts; correlated success/failure traces without query text. Arbitrary free-text redaction is intentionally replaced by withholding. |
| CS-07 | `evals/complaint_api_cases.json`, `complaint_api_fixture.py`, `complaint_api_starter.py` | Five runnable synthetic HTTP cases with content/citation/provider-call assertions and follow-up/recovery checks. E can extend these; production does not import or enable the fixture provider. |

## B → C structured-provider integration

Inject a reviewed provider through `create_app(provider=..., db_path=..., evidence_service=...)`. This is an internal adapter boundary, not another web service. The production app currently constructs `UnavailableProvider`; merely starting MySQL does not wire a provider automatically. Do not use A's SQL-dump validator as a substitute for live SQL.

Provider members:

- `available: bool`: configured capability flag; not an automatic liveness probe.
- `resolve(text)`: read-only, source-backed candidate lookup. The input may contain unmasked local complaint text; do not forward it to a model or log it.
- `revalidate(saved_source_version, received_date, identity)`: recheck selection against the original complaint context and immutable published source version; return the same candidate-result shape.

Synthetic provider result:

```json
{
  "status": "found",
  "source_version": "batch-v1",
  "received_date": "2026-03-01T12:00:00+08:00",
  "candidates": [{
    "system_version": "v1",
    "order_id": 99999,
    "created": "2026-01-01T10:00:00+08:00",
    "citation": {
      "type": "sql",
      "source_id": "sql:orders",
      "ref": "merlion_express.orders",
      "locator": "order:row",
      "record_key": {"system_version": "v1", "order_id": 99999}
    }
  }]
}
```

The adapter accepts `found` with one or more candidates, or `not_found` with an empty list; the API derives ambiguity from the eligible candidate list. Map B's general tool envelope into this shape and propagate failures as exceptions, never as an empty successful search. Keep `source_version` immutable for unchanged evidence and advance it when sources change. Supply the complaint date from evidence, not the current clock or guessed prose. Date-only values may be compared with date-only values; timestamps require offsets and comparable precision. Mixed precision currently fails safely rather than claiming no match. Candidate SQL citation keys must match the candidate identity. Source IDs/refs/locators use compact logical identifiers; their syntax currently permits letters, digits, underscores, dots, colons and hyphens.

## Decisions and operating limits

- Complaint input: nonblank, at most 20,000 characters. Follow-up: nonblank, at most 10,000 characters; at least a message or selected composite identity is required. Extra request fields and incorrectly typed identities are rejected.
- Existing-session complaint submission returns `409 SESSION_CONFLICT`; use the messages endpoint. Missing sessions return 404. Changed source context returns `409 SOURCE_CHANGED`. Concurrent turns use SQLite compare-and-swap and return 409 on a conflict.
- Session storage defaults to ignored `output/api/sessions.sqlite3`, configurable with `CAPSTONE_SESSION_DB`. Safe structured turn markers replace original complaint/follow-up text; the UI cannot reconstruct the pasted original from recovery. This is an explicit privacy/UX tradeoff pending reliable free-text name masking. Retention/access controls remain a separate agreement for any future public deployment.
- Tool calls default to five seconds, configurable up to 15 seconds per call, with at most two stages and four in-flight worker slots per app. Timed-out work retains capacity until it actually ends. Providers must enforce their own network/database deadlines because Python cannot kill a running thread. Automatic retries and POST deduplication are not implemented.
- Cached evidence defaults to project-root `output/unstructured`; `EvidenceService(out_dir=..., source_root=...)` selects another approved local preparation directory/root. Only logical paths inside the configured `data/` tree are accepted for originals. A's files remain unmasked and private; the adapter exposes selected time/driver facts and static policy availability, withholding receiver names, remarks and arbitrary snippets. Guide conditions and rate calculations have not been assessed.
- Request/tool events go through the `merlion.api` logger to the configured logging handlers, with a stderr fallback. Logs contain request/session IDs, fixed tool/route names, status and timing; durable telemetry storage, model token/cost events and daily spend consolidation are pending.
- Health reports sessions available and triage according to provider configuration. It remains degraded while weekly/semantic features are unavailable. This does not certify full resolution assessment. The shared launcher's all-feature live gate remains in place; D's per-feature profiles/retry fixes are still separate frontend work.

## Verification actually run

All checks below ran against the final local source on macOS/Python 3.13:

| Check | Result |
|---|---|
| `python -B -m unittest discover -s backend/api_service/tests -v` | **27 passed** (API, recovery, concurrency, trace correlation and evidence adapter). |
| `python -B -m unittest discover -s scripts/tests -v` | **17 passed**. |
| `python -B -m unittest discover -s backend/unstructured/tests -v` | **70 passed**; existing A source/tests unchanged. |
| `python -B -m evals.complaint_api_starter` | **5 passed** with explicit synthetic provider. |
| Real Uvicorn HTTP/process test | **Passed:** create ambiguous complaint → select candidate → cited synthetic evidence → follow-up → terminate server → restart with default unavailable provider → recover identical saved evidence/citations/history with a fresh request ID. Only test-owned processes were stopped. |
| `git diff --check` | Passed. |

The workspace virtual environment lacked the optional HTTP test dependency. Verification used the existing cached `httpx==0.28.1`, `httpcore`, `certifi` and `sniffio` through a temporary `PYTHONPATH`; no package installation or network download was needed. Teammates should install the existing `requirements-dev.txt` normally before the API tests/starter. No paid calls, client-data runs, frontend builds, Windows/WSL runs or live MySQL integration were performed for this increment.

## Next actions

| S/N | Owner | Task |
| --: | --- | --- |
| 1 | B/C | Implement and wire the reviewed live provider, settle date precision/source-version conventions, then add delivery/GPS/full rate inputs and verified assessment. |
| 2 | D/C | Review the 409/error/privacy choices and source-specific citation rendering; apply the existing per-feature demo/live and retry handoff, then connect the UI. Preserve clarification when the order number is missing, including a free-text continuation path. |
| 3 | E/C | Extend the five-case starter with owned real-data expectations, restart/failure checks and the shared case schema. The five synthetic cases do not establish the capstone's 20-case acceptance gate. |
| 4 | C | Complete policy/rate/answer orchestration, durable telemetry/spend and consumer review; attach PR evidence before marking tasklist items verified complete. |
