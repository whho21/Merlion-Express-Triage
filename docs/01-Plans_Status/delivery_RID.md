# Risks, Issues and Decisions

## R-I-D Legend

- Risk: a potential future problem.
- Issue: a problem already happening.
- Decision: a choice made or awaiting agreement.

## Log

| S/N | R-I-D | Desc | Owner | Date Raised | action/when/progress | Status |
| --: |:--:|---|---|--:|---|:--:|
| 1 | Decision | Team to agree mapping of A/B/C/D to John, Ralph, Jenn Fang and Jeffrey | John | 14 Nov 2026 | confirm owners and all assignments by 17 Nov; balance captain duties and frontend capacity | Open |
| 2 | Decision | Confirm instructor-repository PR/merge and team-backup sync workflow; verify individual commit attribution | John | 14 Nov 2026 | Before 19 Nov checkpoint; confirm target branch and submission process, then rehearse sync | Open |
| 3 | Decision | Confirm React as frontend baseline; any switch to Streamlit changes ownership and integration work | D/team | 14 Nov 2026 | Ratify by 17 Nov; continue existing React scaffold meanwhile | Open |
| 4 | Decision | Choose Python API framework, orchestration approach and retrieval index after package/endpoint checks | C with A/B | 14 Nov 2026 | Agree minimum stack and contracts by 17 Nov; LangGraph and FAISS remain proposals | Open |
| 5 | Risk | Unknown class API capabilities, rates and team budget could constrain OCR, embeddings and model use | C | 14 Nov 2026 | Confirm at 16 Nov briefing; run small measured samples before full processing; report spend daily | Open |
| 6 | Risk | Repeated OCR/extraction runs could consume the API budget | A | 14 Nov 2026 | Name one coordinator for full paid runs; cache by source and configuration; record starts and outcomes | Open |
| 7 | Risk | Brief/package mismatches and source authority or timezone uncertainties may block correct answers | A/B draft; John sends | 14 Nov 2026 | Audit package on 16 Nov; send precise client questions promptly; log pending answers and decisions in client_qa.md | Open |
| 8 | Risk | Data audit may delay backend/frontend integration | C/D | 14 Nov 2026 | Agree synthetic API contracts and fixtures by 17 Nov; replace with verified evidence incrementally | Open |
| 9 | Risk | Frontend work plus eval coordination may exceed D capacity | D/C/team | 14 Nov 2026 | Keep UI to complaint and weekly views; D owns runner, CI and cross-component smoke checks; each owner supplies/fixes cases; John coordinates pitch; review workload daily | Open |
| 10 | Risk | Agent workflow or loaders may become integration bottlenecks | C or B/team | 14 Nov 2026 | B owns candidate lookup and source keys; A/B own provenance and tool retries; C owns orchestration and final-answer checks. Agree handoff fixtures early; reassign bounded work if blocked | Open |
| 11 | Decision | Recommendation-only MVP versus executing refunds or other consequential actions | C/team | 14 Nov 2026 | Agree by 17 Nov and document in architecture; if execution is added, design approval and duplicate-action protection first | Open |
| 12 | Risk | Client data or keys could enter commits, screenshots, traces or portfolio deployment | All | 14 Nov 2026 | Keep client-bearing artifacts and secrets out of Git; inspect staged files and sanitise evidence before each PR | Open |
| 13 | Risk | C has too many cross-cutting responsibilities, while B and D also face dense integration work | John/team | 15 Nov 2026 | D owns thin HTTP routes/models and integration checks; C owns agent services, state and guardrails; protect the first cited complaint flow before weekly analytics; review progress daily | Open |
