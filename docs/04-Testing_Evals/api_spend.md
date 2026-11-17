# API spend log

Team key budget: **US$50 for the whole project** (team key sheet, 16 Nov; spend monitored weekly; HARNESS_CHECKLIST §7).
Costs below are **estimates** from the token counts the API returns × OpenAI list prices
(`backend/unstructured/llm.py`, `PRICES_USD_PER_MTOK`). The provider's usage page is the source of truth.
Each A run also appends a line to `output/unstructured/spend_log.jsonl` (local) and per-call lines to `telemetry.jsonl`.

| Date (SGT) | Who | What | Model | Paid calls | Tokens in / out | Est. US$ | Running total US$ | Budget used |
|---|---|---|---|---:|---:|---:|---:|---:|
| 2026-11-16 | Ralph (A) | Smoke test: 2 POD cards + rate card | gpt-4o-mini | 3 | 77,109 / 649 | 0.0120 | 0.0120 | 0.02% |
| 2026-11-16 | Ralph (A) | Full run: remaining 78 POD cards (3 from cache) | gpt-4o-mini | 78 | 2,006,004 / 9,556 | 0.3066 | 0.3186 | 0.64% |
| 2026-11-16 | Ralph (A) | Rebuild records after two rule fixes (all 81 from cache) | gpt-4o-mini | 0 | 0 / 0 | 0.0000 | 0.3186 | 0.64% |
| 2026-11-17 | Ralph (A) | Vector index build — **refused: HTTP 429 `credit_balance_exhausted`** (also on gpt-4o-mini) | text-embedding-3-small | 0 | 0 / 0 | 0.0000 | 0.3186 | 0.64% |

| 2026-11-17 | Ralph (A) | Vector index built with **local** embeddings instead (numpy, offline) | local-tfidf-chargram-v1 | 0 | 0 / 0 | 0.0000 | 0.3186 | 0.64% |

**17 Nov: the team key reports no credit remaining for every model.** A's own spend is US$0.32, so this was not
A's runs. To raise with John/Leonard; all paid work (A's vector index, C's agent) is blocked until credit is restored.

**A total so far: about US$0.32 of US$50 (0.64%).** All 80 POD cards and the rate card are read and cached;
re-reading them costs nothing unless the prompt or model changes.

Notes:
- One POD card costs about 25,700 input tokens on gpt-4o-mini (images are billed as many tokens on this model),
  so about US$0.004 per card. Re-running is free: answers are cached by image + prompt version + model.
- Other members: add a row per paid run, or point to your own log, so the Captain can total it weekly.
