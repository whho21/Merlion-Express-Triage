# Checkpoints

Tick items as your team completes them; the instructor reviews this file at each due date.

## Checkpoint 1 — due Fri 20 Nov 2026, 17:00 SGT

Updated per 16 Nov team instruction. Instructor baseline files and the release PDF retain the original date; do not edit them. Consult schedules and other deadlines are unchanged unless separately confirmed.

- [ ] Data audit complete: every file in `data/` opened, row/page counts recorded
- [ ] ER diagram of the CLEANED schema (Mermaid, in `docs/`)
- [ ] Trap list: every data-quality problem found so far, with evidence
- [ ] Package checked against the brief: anything the brief mentions that is NOT in the package has been raised with the client by email, and the actual reply or explicitly pending status recorded in `docs/00-Biz_Requirements/client_qa.md` (drafts are not sent questions)
- [ ] Architecture proposal (Mermaid, in `docs/`)
- [ ] All five developers have committed substantive work under their own GitHub identities

## Checkpoint 2 — due Mon 23 Nov 2026, 09:00 (reviewed at Consult 3, 13:00 on Zoom)

- [ ] Ingestion + retrieval working end-to-end on at least 2 source types (one must be images)
- [ ] One demonstrable answer WITH citation of its source
- [ ] Vision/OCR pipeline extracting from the scanned documents
- [ ] API spend checked against budget

## Demo hardening — Consult 4 Tue 24 Nov 10:00 (demo rehearsal) · final sprint Thu 26 Nov 09:00–12:00

- [ ] Agent/tool-use layer complete; cross-source questions answered at query time
- [ ] Guardrails in code (see HARNESS_CHECKLIST.md) and eval suite (20+ cases) passing
- [ ] Data quality report finished
- [ ] Dress rehearsal: someone hostile has tried to break the app
- [ ] Pitch (5 min) rehearsed and timed

## Demo day — Fri 27 Nov 2026, 09:00–13:00, NTU@one-north SR902

Per team: 5-minute pitch · 5-minute live demo · Q&A from a judging panel role-playing your customer. Slot order is announced at Consult 4; bring your own laptop and charger.

Ownership and internal gates: [team plan v0.5](../01-Plans_Status/Capstone_TEAM_PLAN_v0.5.md). E verifies consolidated evidence; each owner supplies and fixes their component.

## Internal preparation and accountable owners

These support the official checkpoints; they do not add instructor requirements or change consult dates.

| Gate | Preparation / owner |
|---|---|
| 17 Nov contracts | Ralph: chunking/embedding/retrieval design and metadata; Jenn Fang: source keys/tool schema; John: API/session/telemetry and runner starter; Jeffrey: customer scenarios; Wai Hong: setup reconciliation |
| 18–19 Nov early integration | First five runnable evals and thin cited flow; Wai Hong owns runner/results, each owner fixes their layer |
| 20 Nov, 17:00 Checkpoint 1 | Ralph/Jenn Fang audit and traps; Jenn Fang cleaned ER; John architecture and verified client log; Jeffrey journey/acceptance examples; Wai Hong package/setup/eval evidence; all five substantive commits |
| 20 Nov internal rehearsal → 23 Nov, 09:00 Checkpoint 2 | Ralph image extraction, Jenn Fang cited data tool, John API/agent, Jeffrey React, Wai Hong integrated verification; John checks actual spend and merged submission |
| 23 Nov internal presentation target | Jeffrey drafts business-value narrative and demo storyline; A/B/C verify facts and current limitations |
| 24 Nov rehearsal | Wai Hong consolidates ≥20 passing evals including required refusals; owners fix failures. Jeffrey leads timed five-minute pitch; John technical Q&A. Choose and record operator/backup; rehearse restart and failure recovery |
| 26 Nov final sprint | Jeffrey finalises deck; Wai Hong verifies runbook; John confirms submission and technical claims; all provide final evidence |
| 27 Nov demo | Jeffrey leads presentation/client-facing demo; rehearsed operator runs UI; John technical Q&A; Ralph/Jenn Fang source explanations; Wai Hong runbook/recovery/eval support |

All required acceptance, identity and refusal cases must pass. Extra passing cases cannot conceal a known critical failure. A missing-source abstention is distinct from a policy refusal. Client questions remain drafts until actually sent; pending answers and blocked features stay explicit.
