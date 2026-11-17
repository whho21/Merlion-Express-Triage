# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-17 (SGT)
**Topic**: Embeddings + FAISS + SQLite vector index for A's retrieval (team decision 17 Nov)

## Scope

**Built and tested; the real index is NOT built yet — the team API key has no credit (see Blocker).**

- `backend/unstructured/vector_index.py` — SQLite holds every chunk (text, source, exact locator, category, date,
  order numbers, guide version) plus an embedding cache; FAISS (`IndexFlatIP` on normalised vectors = cosine) holds
  the vectors keyed by SQLite row id, so every vector hit maps back to a verifiable citation.
- Chunks are natural units: one per complaint email (subject + body) and one per Resolution Guide rule/note
  (90 + 12 = 102). No splitting or overlap: the longest chunk is ~310 characters.
- **PDPA:** text is masked (`masking.mask_text`) before it is sent to the embedding endpoint, and so is the user's
  question. The full text stays only in the local SQLite file under `output/` (git-ignored).
- **Cost control:** vectors cached in SQLite by sha256(model + masked text) — a rebuild embeds only new/changed
  chunks. Each embedding call logs tokens + cost (no text) to `telemetry.jsonl`; each build is added to `spend_log.jsonl`.
- **Stale guard:** the index stores the sha256 of `emails.jsonl` + `policy_chunks.jsonl`; if they change, search
  reports `INDEX_STALE` and uses keyword until `build_index` is rerun.
- **Search (`search.py`)**: `mode="hybrid"` (default) fuses keyword ranks and vector ranks (reciprocal rank fusion,
  k=60); `mode="vector"` FAISS only; `mode="keyword"` never calls the AI. Exact paths are unchanged:
  `category` → that rule row, `order_number` → that order's emails. Every result now has a `retrieval` field
  (`hybrid:keyword+text-embedding-3-small`, `vector:…`, `keyword`, `keyword (fallback: <CODE>)`, `category`,
  `order_filter`). If the vector side is unavailable, hybrid falls back to keyword and says why; vector mode returns
  `failed` with the code instead of guessing.
- `llm.embed_texts` (batched, 3 bounded retries, cost per call). `ask.py` now prints the search method.
- **Install** for vector search: `pip install -r backend/unstructured/requirements.txt` (faiss-cpu, numpy).
  Without them everything else still runs and search says `keyword (fallback: NO_FAISS)`.
- **Checks:** 84 unit tests pass (14 new: build, cache reuse, masking of what leaves the machine, kind filter,
  threshold, stale refusal, exact email citations from vector hits, order filter, fallbacks on endpoint failure /
  no index / no faiss, keyword mode never calls the embedder, bad mode). Evals: 18/18 pass on real data (keyword
  fallback); A-E19..A-E21 added for vector behaviour and **PENDING** until the index is built.

## Blocker — team API key out of credit (found 17 Nov)

`python -m backend.unstructured.build_index` got HTTP 429 `insufficient_quota / credit_balance_exhausted`
("You have no credits remaining") for every embedding model **and for gpt-4o-mini chat** — so it affects C's agent
too, not only A. A's recorded spend is US$0.32 of the US$50 budget, so the credit was not used up by A's runs. It may
be the account behind the key rather than our usage. **Raise with Leonard today.** Do not switch to the class key.

## Remaining (once credit is restored)

1. `python -m backend.unstructured.build_index` — expected cost under US$0.001 (102 short texts).
2. Calibrate `MIN_SIMILARITY` (provisional 0.30) on relevant vs unrelated questions.
3. Measure keyword vs vector vs hybrid on the 16 questions from the 17 Nov guide handoff + Jeffrey's realistic
   questions; record top-1 accuracy here and pick the default mode from the numbers.
4. Run evals: A-E19..A-E21 should move from PENDING to PASS (or the expectation is wrong and gets fixed).

## Next Step

- John / Leonard: restore API credit (blocks C's agent as well as A's index).
- John (C): results now carry `retrieval`; show it in traces. Default `mode="hybrid"` is safe today because it falls
  back to keyword.
- Everyone who wants vector search locally: install `requirements.txt`, run ingest, then build_index.
