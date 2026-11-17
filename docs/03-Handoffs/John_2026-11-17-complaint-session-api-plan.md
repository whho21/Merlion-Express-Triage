# Complaint/session API implementation plan

Date: 17 Nov 2026 (SGT). Requested by Developer C. Implementation delegated to GPT-6.1 Terra, low reasoning (the available light setting).

## Sources and scope

Read `docs/02-Design/api-catalog_v0.9.1.md` sections 2–4, 6–8; `frontend-ui-contract-draft.md`; `contracts_2026-11-16.md`; and the 17 Nov API/mock, guide/client-answer, PR11-review and architecture handoffs. Existing FastAPI bootstrap is implemented; five domain routes were outstanding before this change.

This increment implements the three complaint/session routes. Weekly endpoints, B's case loaders/views, frontend profile fixes, optional semantic retrieval and paid model/extraction runs are outside this increment. Reuse A's file-backed tools. B owns live MySQL/candidate facts; define an injectable structured-tool boundary and report an unavailable implementation honestly. Never turn an unavailable lookup into a successful no-match. A SQL-dump validation helper is not a live MySQL tool.

## Ordered requirements and checks

| ID | Source | Requirement | Implementation/check |
|---|---|---|---|
| CS-01 | HTTP-01, ComplaintResult | Validated `POST /api/complaints`; stable display-ready response fields, fresh request ID and opaque session ID; normal, ambiguous, partial, not_found, refused and failed outcomes. | Pydantic models, route/service; synthetic provider HTTP checks for outcomes and invalid input. |
| CS-02 | HTTP-02, TOOL-05/14 | Validated follow-ups and candidate selection scoped to existing session; never accept unoffered/ineligible composite keys or overwrite original complaint on resubmit. | Service and persisted workflow; foreign/future candidate, unknown session and conflicting/context-changing input checks. |
| CS-03 | HTTP-03, TOOL-14 | SQLite persistence of sanitised messages, result, eligible candidates and source references; restart recovery without tool/model reruns; isolated sessions and fresh recovery request IDs. | Temporary SQLite databases; create a new app/store against same file and recover; isolation checks. |
| CS-04 | sections 3.2, 6, API/mock handoff | Consistent safe validation/dependency/internal errors; bounded failures, no raw exceptions or personal data; preserve retryability and keep health truthful. | Invalid fields/IDs, failing/slow tools, malformed outputs and health checks. |
| CS-05 | sections 3.3, 4.1–4.2, PR11 handoff | Adapt A's envelopes/citations, inspect status and extraction outcome, verify citation references, preserve conflicts and abstain when supporting facts/rules are absent. | Injected cited tool results and temporary A evidence files; no fabricated order/rate/refund/GPS evidence. |
| CS-06 | sections 6–7, A masking handoff | Deterministic refusals and safe browser/persistence output, including known personal-name fields; no raw input in telemetry; per-request/tool timing/status traces. | Refusal before dependency calls, personal-data checks on response/store/log, missing-source and output validation checks. |
| CS-07 | contracts acceptance | Synthetic API fixtures and small runnable evaluation starter; concrete consumer setup and coverage handoff. | Run fixture examples/starter and focused tests; record actual results and outstanding B/A/model integration. |

Keep `backend/api_service/` simple: focused modules only as needed, no new web service. Defaults must not fabricate data or silently use demo fixtures. No new runtime dependencies are needed for SQLite or A's evidence adapters. Make deterministic evidence-backed functionality explicit; leave unsupported policy assessments as abstention. Do not represent this increment as completed model orchestration or live SQL integration.

## Review and delivery

Background agent owns API implementation, tests and synthetic eval artifacts. Parent owns final integration review, documentation reconciliation, executed verification and completion handoff. Preserve unrelated changes; do not commit or publish. Verify existing startup/API checks remain compatible, and document any launcher's stricter all-feature live gate separately from direct API availability.
