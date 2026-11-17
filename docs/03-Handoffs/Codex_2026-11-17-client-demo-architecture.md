# Client demo architecture — diagram handoff

**Date:** 17 Nov 2026, SGT. **Scope:** first-release design, not an implementation/readiness claim.

## Artifacts

- [Native draw.io source](../02-Design/merlion-express-technical-architecture-codex-20261117-114201.drawio) — editable components, logical store groups and connected edges.
- [Embedded editable SVG](../02-Design/merlion-express-technical-architecture-codex-20261117-114201.drawio.svg) — exported by draw.io Desktop; accessibility title/description included.
- [Diagram page](../02-Design/architecture_unstructured.md) — new diagram first; Ralph's original contribution retained verbatim in a collapsed section.

## Decisions and source evidence

| Boundary | Evidence / release decision |
|---|---|
| Structured ingestion | `database/createdb_seed_sql_data.md`, `docker-compose.yml`, `database-design_2026-11-16.md`: preserve `drivers`, `orders`, `deliveries`; add only `raw_case_log`, `clean_cases`, `clean_case_members` and two weekly views. Preserve all 505 raw workbook rows before business deduplication. Application DDL/loaders remain pending. |
| Unstructured ingestion | `backend/unstructured/ingest.py`, `extract_images.py`, `policy.py`, `sqlref.py`: reuse existing text/Excel parsing and cached vision; SQL validation reads the dump. Four JSONL evidence stores retain original source locators/confidence. No SQL evidence migration in release 1. |
| Retrieval | Existing `search.py` supplies lexical/category retrieval. Chunk masking, embedding endpoint capability check, versioned FAISS index and query-time semantic integration are pending. Only email/guide text is embedded; POD/rates remain exact tools. Preserve original locators alongside masked text; regex masking needs additional name coverage. |
| Backend | Draft API, exact order/SQL/GPS tools, deterministic rate/policy checks, grounded answer model, citation/PII checks and honest failures. API owns local SQLite session save/restore. No money movement, customer messaging or operational mutation. Sessions, routes and integrated services are not implemented in this checkout. |
| Frontend | `frontend/src/App.jsx`, `api/client.js`, `config.js`: triage, weekly and static explainer screens exist; draft paths use `/api`. Triage submits complaints, sends follow-ups/candidate selections and fetches sessions. Weekly calls `/weekly/weeks` and `/weekly?week_start=...`. Screens remain in mock mode. |
| Client authority | `client_qa_v02.xlsx`, Client Q&A Q01–Q08, plus workbook Resolution Guide rows 5–18: canonical complaints, guide v2 for all dates, five town-derived ops zones distinct from pricing zones, supplied POD limits/latest attempt, investigated GPS clock alignment, retrospective April card, inclusive bands, standard service, derived CBD/PH inputs and referred unknown attempt counts. |
| Capstone harness | `CLIENT_BRIEF.md`, `HARNESS_CHECKLIST.md`: all supplied source types, query-time grounding, cited conflicts/abstentions, input/output guardrails, bounded failures, persistent multi-turn sessions, trace/spend records and evals. Diagram lists ≥20 evals, ≥2 refusals and ≥5 kill-shot phrasings as acceptance work, not completed results. Existing Mermaid diagrams remain available in the original contribution and `architecture_overall.md`. |

## Verification

- Native XML and SVG parse; SVG heuristic check passes.
- Exported SVG was reopened with draw.io Desktop: same 74 vertices and 31 source/target-connected edges as the native file.
- Actual SVG rendered in a local browser; full preview inspected for store shapes, routing, text clipping and label clearance. Minimum rendered font is 20 px; at 1600 px displayed width this is 13.33 px.
- Palette: Paper/Ink/Muted ink and Paper body variant, plus blue, cream and rose. No external image/font dependencies; local model metadata remains embedded.
- Document links and whitespace checks pass. No backend code changed, application tests run, paid extraction performed or demo acceptance result claimed.

## Next implementation work

B delivers the three case-table migrations/loaders, two views, validated SQL/GPS tools and reference seeds. A/C agree embedding capability and evaluate semantic retrieval against Ralph's lexical baseline. C implements API, guards, sessions, answer validation and telemetry; D connects existing screens; E verifies the capstone checks with recorded results.
