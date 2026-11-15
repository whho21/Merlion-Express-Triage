# Team 2 Plan — Merlion Express Capstone

**Status:** DRAFT for John's and the team to review. Nothing here is final until John approves it.

**Prepared:** Fri 13 Nov 2026

**Team:** John Phang (Captain), Ralph, Jenn Fang, Jeffrey Kong

**Next sync:** Team meeting, Tue 17 Nov, 2 PM

---

## 1. What this plan consolidates

| Source | What it said | 
| --- | --- |
| Discord, John's post (LEO>>) | Stage 1 "Data foundation" is done by all four and blocks everything else. Then four workstreams A to D mapped to the Harness Checklist. Streamlit frontend is not a separate workstream. Docs, data quality report, pitch and post-mortem are shared. Agree tool signatures, citation format and state keys before anyone codes. 
| WhatsApp, John | Expand the guide into tasks for 4 persons and save it as markdown for use throughout the capstone. Scope must cover: ingestion pipeline (ETL/ELT), frontend (John suggests ReactJS), evals, backend engine services, and the chunking / embedding / semantic search / LLM chain. John has raised a PR to merge the scaffolding; option A is to merge it first, then branch as `feature/abc_xyz`; option B is to start now and resolve conflicts later. |
| Repo docs | `CLIENT_BRIEF.md`, `HARNESS_CHECKLIST.md`, `CHECKPOINTS.md`, `README.md` |
| Github (work progress & submission  repo) | https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express |
| Team GitHub for backup | https://github.com/NTU-AIE1F-Team6/capstone-merlion-express | 
| LEO course agent | LEO http://54.254.238.205/ <br>user: blank<br>access: see discord `https://discord.com/channels/1569548903500611684/1570294942998331403/1570803169825660989` |


On evals: they are in scope. The Harness Checklist item 8 requires 20+ cases run by one command, including two correct refusals. They sit in Workstream D below.

---

## 2. Decisions needed from John

| #   | Decision                                 | Options                                                                                  | Note                                                                                                                                                                        |
| --- | ---------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Who takes A, B, C, D                     | See section 4                                                                            | Jeffrey's preference is D; open to reassignment                                                                                                                             |
| 2   | Frontend                                 | Streamlit (Discord post) or ReactJS (John's suggestion)                                  | Streamlit is quicker and stays in Python. ReactJS looks better but needs a separate API layer and more hours. The demo is 5 minutes and marks are on the harness.           |
| 3   | Git workflow                             | A: merge scaffolding PR first, then feature branches. B: start now, fix conflicts later. | Jeffrey recommends A. His local clone has no changes, so after the merge he only needs `git pull`.                                                                          |
| 4   | Starter files                            | See section 7                                                                            | Which of these does the scaffolding PR already contain? https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express/pull/1                                           |
| 6   | Who sends client questions               | One named person                                                                         | Replies take up to two working days, so questions should go out by Tue 17 Nov.                                                                                              |
| 7   | Who runs paid jobs on the shared API key | One named person per job                                                                 | The OCR run over 80 scans is the largest single cost.                                                                                                                       |
| 5   | First-commit deadline                    | Discord post says Mon 2 Nov; `CHECKPOINTS.md` says before Thu 19 Nov, 09:00              | 2 Nov has passed, so 19 Nov is assumed. Confirm with the instructor. **John**: GitHub repo is the golden source. Discord posts are suggestions from LEO course guide agent. |

---

## 3. Stage 1 — Data foundation (all four, Mon 16 to Thu 19 Nov)

This stage blocks all workstreams. To avoid four people auditing the same file, each person profiles one group of sources and logs traps in `docs/trap_list.md`.

| Source group | Files | Things to establish | Owner |
|---|---|---|---|
| S1 Orders and deliveries | `sql/merlion_ops.sql` | Tables, row counts, how v1 and v2 are marked, duplicate order numbers, postal code type, migration gaps around February | TBC |
| S2 Case log, policy and rates | `tabular/` (CS case log, Resolution Guide), `images/rate_cards/` | Whether the Resolution Guide is present and complete, rate card versions, case log versus SQL disagreements | TBC |
| S3 GPS | `logs/gps_pings_sample.jsonl` | Ping count (about 60k), fields, timezone, measured offset against delivery times | TBC |
| S4 POD scans and emails | `images/proof_of_delivery/` (80), `docs/complaint_emails/` (90) | File counts, unreadable scans, orders with no POD, emails whose order number matches neither or both systems | TBC |

**Checkpoint 1 outputs (due Thu 19 Nov, 09:00)**

| Output                                     | File                   | Owner                                |
| ------------------------------------------ | ---------------------- | ------------------------------------ |
| Data audit with counts                     | `docs/data_audit.md`   | Each source owner adds their section |
| Trap list with evidence                    | `docs/trap_list.md`    | Everyone; D compiles                 |
| ER diagram of the cleaned schema (Mermaid) | `docs/architecture.md` | B                                    |
| Architecture proposal (Mermaid)            | `docs/architecture.md` | C                                    |
| Client questions sent, answers logged      | `docs/client_qa.md`    | D, with John's sign-off              |
| Everyone has committed                     | git history            | All four                             |

---

## 4. Four workstreams (from Tue 17 Nov, after contracts are agreed)

### A — Ingestion and retrieval (unstructured sources)

- **Checklist items:** 1 Grounding, 2 Citations
- **Scope:** everything that turns images and documents into something searchable.
- **Tasks**
  1. Vision/OCR pipeline for POD scans: extract order number, timestamp, recipient, signature present; store with the image file name. Run each image once and cache the result.
  2. Vision/OCR for rate cards into a rate table.
  3. Chunk and embed complaint emails and the Resolution Guide into a FAISS index.
  4. Metadata on every chunk (file name, position) so answers can cite.
  5. Retrieval functions: `search_policy`, `search_emails`.
- **Mermaid diagram owned:** ingestion data flow.
- **Checkpoint 2 contribution:** OCR pipeline working; images ingested end to end.

### B — Structured data and tools

- **Checklist items:** 1 Grounding, 4 Error handling
- **Scope:** the cleaned database and every tool that reads it.
- **Tasks**
  1. ETL scripts from raw to cleaned tables: unified order key `(source_system, order_no)`, one timezone, postal codes as text. Scripts must be re-runnable.
  2. Load GPS pings into a table indexed by driver and timestamp.
  3. SQL tools: `get_delivery_history`, `get_pod`, `get_gps_window`, `get_rate`.
  4. Cross-source joins done in code, not by the model.
  5. Weekly drivers and zones complaint aggregate.
  6. Error handling in every tool: a failure returns "could not check X", never a made-up value.
- **Mermaid diagram owned:** ER diagram of the cleaned schema.
- **Checkpoint 2 contribution:** SQL source working end to end with one cited answer.

### C — Agent core

- **Checklist items:** 5 State, 6 Human-in-the-loop
- **Scope:** the LangGraph graph that drives one complaint from email to recommendation.
- **Tasks**
  1. Graph for the five steps: resolve order, gather evidence, reconcile sources, decide per Resolution Guide, cite and gate.
  2. Order resolution when a number exists in both v1 and v2 (use date, name, address; ask if still ambiguous).
  3. Conflict handling, for example POD says delivered but GPS disagrees: state the conflict and which source is trusted.
  4. Checkpointer so multi-turn context and restarts work.
  5. Approval gate (`interrupt()`) before refund or compensation.
  6. Assemble citations from tool results into the final answer.
- **Mermaid diagram owned:** sequence diagram of one complaint.
- **Checkpoint 2 contribution:** tool loop calling at least two tools.

### D — Harness layer

- **Checklist items:** 3 Guardrails, 7 Observability, 8 Evals
- **Scope:** everything that proves the app is safe, measurable and correct.
- **Tasks**
  1. Output guardrail in code: filter personal data (phone numbers, addresses, ID numbers).
  2. Input guardrail: deterministic refusal of out-of-scope requests.
  3. Identify the "kill-shot question" and test it in five phrasings.
  4. Eval suite: 20+ cases, one command, at least two refusals; rerun after each significant change and commit the output.
  5. Logging per request: tool calls, latency, tokens. Cost meter and running spend log against the API budget.
  6. Compile `docs/trap_list.md` into the one-page data quality report; keep `docs/client_qa.md` current.
- **Mermaid diagram owned:** guardrail and logging flow (optional third diagram).
- **Checkpoint 2 contribution:** API spend checked and recorded; first 5 eval cases written.

### Frontend

Not a separate workstream. Whoever finishes first takes it; the backend stays pure Python and the UI only calls it. Streamlit or ReactJS is decision 2 above.

---

## 5. Shared across all four

- Architecture docs and Mermaid diagrams, each person owning the diagram for their area.
- One-page data quality report (D compiles, everyone contributes traps).
- 5-minute pitch and the post-mortem.
- Commits from every person under their own GitHub account, with `Co-authored-by:` when pairing.

---

## 6. Contracts to agree before anyone codes (proposed for Tue 17 Nov)

These are first drafts. Field names will change once the real schema is seen on 16 Nov.

**Tool signatures**

| Tool | Input | Owner |
|---|---|---|
| `resolve_order` | email text | C (uses B and A tools) |
| `get_delivery_history` | source_system, order_no | B |
| `get_pod` | source_system, order_no | B (data from A) |
| `get_gps_window` | driver_id, start_time, end_time | B |
| `get_rate` | service or zone, weight | B (data from A) |
| `search_policy` | query text | A |
| `search_emails` | query text | A |
| `weekly_complaints` | week_start | B |

**Harness functions (owned by D, called around the tools above)**

D builds no fact-fetching tool, so D has no row in the table above. D owns the functions that wrap every request, and must agree all three contracts below because logging, guardrails and evals read them.

| Function | When it runs | What it does | Who must call it |
|---|---|---|---|
| `check_input` | Before the agent sees a request | Refuses out-of-scope or policy-violating requests without an LLM call | C, at the graph entry |
| `filter_output` | After the agent drafts an answer | Removes personal data; confirms citations are present | C, at the graph exit |
| `log_request` | After every tool call and every model call | Records tool name, latency, tokens and cost | A and B inside each tool; C around model calls |
| `run_evals` | From the command line, after each significant change | Runs 20+ cases and prints pass or fail | Everyone, before merging |

**Common return shape for every tool**

```json
{"ok": true, "data": {}, "sources": [], "error": null}
```

**Citation format**

```json
{"type": "table | file | image", "ref": "deliveries or images/proof_of_delivery/pod_017.png", "locator": "row id, page or line"}
```

**State keys**

`messages`, `email_text`, `order_candidates`, `order`, `evidence`, `conflicts`, `recommendation`, `approval_status`, `citations`, `usage`

---

## 7. Starter files (proposal, pending John's scaffolding PR)

To be created only for whatever the scaffolding PR does not already include, on a branch named `feature/docs_skeleton`.

| File | Purpose |
|---|---|
| `docs/client_qa.md` | Every client question and answer (required by the brief) |
| `docs/trap_list.md` | Every data problem, with evidence and decision |
| `docs/data_audit.md` | Row, page and file counts per source |
| `docs/architecture.md` | Mermaid diagrams |
| `docs/TEAM_PLAN.md` | This plan |
| `docs/package_checklist.md` | Items the brief mentions, to tick against the zip on 16 Nov |
| `evals/README.md` | Placeholder so the folder is tracked |

---

## 8. Timeline

| Date | Event | Team output |
|---|---|---|
| Mon 16 Nov | Briefing; data zip and API key released | Data loaded; Stage 1 starts |
| Tue 17 Nov, 2 PM | Team meeting | Roles confirmed; contracts in section 6 agreed; client questions sent |
| Thu 19 Nov, 09:00 | Checkpoint 1 | Section 3 outputs |
| Mon 23 Nov, 09:00 | Checkpoint 2 | Two source types end to end (one is images), one cited answer, OCR pipeline, spend checked |
| Tue 24 Nov, 10:00 | Consult 4, demo rehearsal | Agent layer complete, guardrails in code, 20+ evals passing |
| Thu 26 Nov, 09:00–12:00 | Final sprint | Data quality report, hostile dress rehearsal, timed pitch |
| Fri 27 Nov, 09:00–13:00 | Demo, NTU@one-north SR902 | Pitch, live demo, Q&A |

---

## 9. Open questions

| Question | For |
|---|---|
| What is the API budget, and is there a page showing spend? | Instructor, 16 Nov |
| Are open-source OCR libraries allowed alongside the class endpoint? | Instructor, 16 Nov |
| Is anything the brief mentions missing from the zip (Resolution Guide, `logs/` folder)? | Client, by email, after checking the zip |
| Which timezone does each system record in? | Client, after measuring the offset |
| Which system is authoritative when v1 and v2 disagree? | Client, after the audit |
