# TOOL-05 live SQL provider — reference implementation handoff

- **Date:** 17 Nov 2026 (SGT).
- **From:** John Phang (C).
- **To:**
    - Jenn Fang (B — adopt ownership, extend and verify)
    - Ho Wai Hong (E — runner cases for the live flow)
    - Jeffrey Kong (D — UI verification against the live flow)
- **Status:** implemented, unit-tested and verified end-to-end against live local MySQL; not committed as a PR and no consumer acceptance claimed yet. Ownership transferred from B to C on 17 Nov (agreed with Jenn; RID item 20) — this is C's component; B's data-owner review is still requested.

## What this is

A live implementation of TOOL-05 `resolve_order` behind the injectable provider
boundary recorded in the [complaint/session handoff](John_2026-11-17-complaint-session-api.md)
("B → C structured-provider integration"). With it injected, HTTP-01/02/03 run a
real flow: complaint → live MySQL candidate resolution → cited POD/policy
evidence from A's published files → follow-up → restart recovery.

## Files

| File | Purpose |
|---|---|
| `backend/api_service/sql_provider.py` | `MySqlProvider` (`available`, `resolve(text)`, `revalidate(version, received_date, identity)`), `SqlProviderError`, env-config |
| `backend/api_service/tests/test_sql_provider.py` | 10 unit tests on a fake connection, incl. the contract test: provider output passes the API's strict `validate_source` |
| `scripts/check_sql_provider.py` | Read-only live smoke check (table counts + one resolve round trip, no personal data printed) |
| `scripts/run_api_demo.py` | Existing synthetic-provider demo launcher (unchanged) |

`backend/api_service/requirements.txt` gained `mysql-connector-python==9.5.0` (installed in the workspace `.venv`).

## Contract compliance

- Reuses A's `ORDER_RE`/`order_references`: `V1-20095` restricts the system version; unqualified `order 20095` makes both v1 and v2 eligible (the API then derives ambiguity).
- Provider shape exactly as specified: `{status: found|not_found, source_version, received_date, candidates[{system_version, order_id, created, status, citation{type: sql, source_id: "sql:orders", ref: "merlion_express.orders", locator: "order:row", record_key{system_version, order_id}}}]}`.
- `source_version` is a deterministic fingerprint of the published `orders` data (`COUNT` + `CRC32` aggregate, SHA-256 prefix, e.g. `orders-74167e6625448fd3`). Immutable while data is unchanged; advances on any change, so the API correctly returns `409 SOURCE_CHANGED` for stale sessions.
- `received_date` is the current **Asia/Singapore calendar date, date-only** (`YYYY-MM-DD`), matching `orders.order_date` (a MySQL `DATE`) so date-vs-date precision applies. Documented limit: a pasted complaint text carries no trusted send date; case-log dated flows must pass their own date.
- Failures raise (`SqlProviderError`) and become `503 DEPENDENCY_UNAVAILABLE`; a genuine no-match is `not_found` with an empty list; duplicate composite identities are treated as a data defect, not ambiguity.
- No personal columns are selected or returned (no customer name, phone, address, postal). Complaint text is never forwarded to a model or logged.
- Candidate cap: > 50 candidates fails honestly (the API rejects more than 50 anyway).

## Verification actually run

All against local MySQL (`root`, port 3306, database `merlion_express` seeded from `data/team2_merlion_express_package/sql/merlion_ops.sql`) on macOS/Python 3.13:

| Check | Result |
|---|---|
| `python -B -m unittest discover -s backend/api_service/tests` | **37 passed** (27 existing + 10 new). |
| `python -B -m unittest discover -s scripts/tests` | **17 passed**. |
| `python -m scripts.check_sql_provider` (live DB) | **found**: `v1:20001 created=2025-10-01 status=DELIVERED`, fingerprint `orders-74167e6625448fd3`. |
| Live HTTP journey: `POST /api/complaints` "My parcel V1-20095 is late…" | `partial`; 4 citations: SQL from live MySQL, 2 POD image field citations (delivered `2025-10-02T16:16`, driver `DRV006`), 1 guide citation (`sheet:Resolution Guide\|row:5`). |
| Live HTTP journey: unqualified `order 20001` | `ambiguous` — 2 candidates (`v1:20001` created 2025-10-01, `v2:20001` created 2026-02-01) with 2 SQL citations; selection of `v2:20001` revalidated OK. |
| Real Uvicorn stop/restart on the same session DB | **Recovered**: `recovered: true`, fresh request ID, identical order/evidence/citations, sanitised messages, follow-up answer preserved, no provider re-query. |

Database facts observed while verifying: 11,499 v1 + 14,334 v2 orders; **11,499 order IDs exist in both systems** (the v2 migration restarted numbering), so unqualified order numbers will resolve as ambiguous by design.

## Local setup notes (workspace-specific)

1. **Credentials:** the launcher `start.sh` only probes port 3306; it does not validate credentials. This workspace's local MySQL uses `CAPSTONE_DB_PASSWORD=root`. Config via env: `CAPSTONE_DB_HOST/PORT/USER/PASSWORD/NAME` (defaults `127.0.0.1/3306/root/capstone/merlion_express`).
2. **POD source paths:** A's published refs are `data/images/...` (his package unzipped directly into `data/`). Where the package lives at `data/team2_merlion_express_package/`, create the supported alias:
   ```bash
   ln -s team2_merlion_express_package/images data/images
   ```
   Without it, POD evidence is `failed` ("cached source could not be verified") because the manifest-hash check cannot open the original. Hash verification passed after the alias, confirming A's bytes are unchanged.
3. **Category classification** uses A's keyword rules (`late`, `where is my parcel`, `COD`, `missing`, …); test text must contain a trigger keyword or policy evidence is honestly `not_found` (`unclassified` has no guide rule).

## Ownership

Ownership of this component transferred from B to C on 17 Nov 2026, agreed with Jenn (recorded as RID item 20). C implements and owns the provider and adapter; Jenn retains data loading, counting/zone definitions, weekly views and analytics. Her review of this module is still requested — she is the owner of the data it queries — and the two shared interface decisions (source_version/batch-publication semantics, date precision) remain joint.

## B (Jenn) — requested review and data-side next steps

1. Review this module as the data owner (adoption no longer required); flag anything that conflicts with your loader or batch-publication plans, especially the `source_version` fingerprint approach and the arrival-date `received_date` choice.
2. Settle the two joint interface decisions with C before your loaders land.
3. Continue with your task-5/6 scope: idempotent case-table loaders, weekly views and delivery/GPS/rate lookups (TOOL-06/07/09 can follow this module's pattern when you build them, or hand the pattern to C to implement against your tools).
4. Supply a repeatable, idempotent seeding/loader script so teammates reproduce the DB without the manual import (your task 1/5 scope).
5. Add integration tests against your own seeded instance; the fake-connection unit tests do not cover SQL syntax, charset or connection timeouts.

## C follow-ups (John)

- Commit this increment with the verification table above as PR evidence before marking tasklist items.
- Note in the API catalog review that the "Known implementation gaps" item for the live provider is now implemented pending B adoption.

## D (Jeffrey) / E (Wai Hong)

- **D:** the 8001-style demo (`scripts/run_api_demo.py`) now has a live-SQL twin: run the API with `create_app(provider=MySqlProvider())` and point React at it with `VITE_USE_MOCK=false`. Use a real order number from the seeded data. Label non-demo-profile responses accurately.
- **E:** add runner cases covering: qualified-number direct resolution, unqualified-number ambiguity → selection, MySQL down mid-request → `503` (not `not_found`), and restart recovery on a live session.

## Known limits (unchanged scope boundaries)

- No delivery/GPS/rate evidence cards, no recommendation (`TOOL-12/13` pending), no weekly endpoints, no POST deduplication, no durable telemetry/spend consolidation.
- Live triage dates use the arrival date (see above); historical case-log triage is B's dated flow.
- MySQL state is the instructor dump as imported; periodic client batches are a separate promotion decision.
