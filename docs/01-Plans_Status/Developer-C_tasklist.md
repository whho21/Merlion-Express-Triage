# Tasklist — Developer C

**Owner:** pending team confirmation
**Scope:** Agent services, sessions and runtime harness

## Task Legend

- ⏳ — waiting to start
- 🚧 — in progress
- ✅ — completed
- 🙅 — cancelled

The A–D to named-person mapping is still open in `delivery_RID.md` (item 1). Update the owner line after the team agrees it. Dates are Singapore time. Mark a task complete only after its deliverable and check are available; link the PR or evidence in the task text when done. Client data and keys stay out of Git.

## Tasklist

| S/N | Task / evidence of completion | Planned End | Done |
| --: | --- | :-- | :--: |
| 1 | Agree service-to-route/tool/error/citation/session and minimal telemetry contracts with A/B/D; publish synthetic success and failure examples in `docs/02-Design/contracts.md` | 17 Nov | ⏳ |
| 2 | Create backend shell and smoke-test class endpoint after key release; record capabilities, limits and measured spend | 16–17 Nov | ⏳ |
| 3 | Write architecture proposal and complaint-flow Mermaid diagram in `docs/02-Design/architecture.md`; define recommendation-only boundary | 19 Nov, 09:00 | ⏳ |
| 4 | Implement complaint/session and weekly-summary service methods behind D’s HTTP routes; review one synthetic React → route → service flow | 17–18 Nov | ⏳ |
| 5 | Consume B’s candidate-order lookup; handle clarification and unresolved identity in the workflow without guessing source system | 20–23 Nov | ⏳ |
| 6 | Orchestrate A/B tools at question time, reconcile evidence, recommend only with policy support and validate final-answer citations against tool references | 23–24 Nov | ⏳ |
| 7 | Persist sessions and demonstrate follow-up plus restart recovery; catch tool failures and return honest partial answers | 24 Nov | ⏳ |
| 8 | Implement deterministic input refusals, final-output checks, API-key protection and backend/model telemetry; A/B own source retries and tool telemetry | 24 Nov | ⏳ |
| 9 | Contribute at least eight workflow/guardrail eval cases, including five kill-shot phrasings and two refusals; own fixes | 24 Nov | ⏳ |
| 10 | Document backend startup/recovery, supply trace and model spend evidence; give John the facts needed for daily total and pitch | 26 Nov | ⏳ |
