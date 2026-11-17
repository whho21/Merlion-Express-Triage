# Handoff

**From**: Ralph (Developer A)
**Date-Timestamp**: 2026-11-17 (SGT)
**Topic**: Embeddings + FAISS + SQLite vector index for A's retrieval (team decision 17 Nov)

## Scope

**Built, indexed on the real data, measured.** Because the team API key has no credit (see below), the team said
"ignore the API, use what we have": the index uses **local embeddings computed with numpy** (free, offline). The
API embedding model is one setting away (`A_EMBED_MODEL=text-embedding-3-small`) once credit returns.

- `backend/unstructured/vector_index.py` — **SQLite** holds every chunk (text, source, exact locator, category, date,
  order numbers, guide version) plus an embedding cache; **FAISS** (`IndexFlatIP` on normalised vectors = cosine)
  holds the vectors keyed by SQLite row id, so every vector hit maps back to a verifiable citation.
- `backend/unstructured/local_embed.py` — **local embeddings** (`local-tfidf-chargram-v1`): TF-IDF over hashed word
  unigrams/bigrams + character 3–5-grams, 16,384 dimensions, IDF fitted on the indexed corpus and saved next to the
  index so queries use the same transform. Handles typos and word forms; does **not** know synonyms.
- Chunks are natural units: one per complaint email (subject + body) and one per Resolution Guide rule/note
  (90 + 12 = 102). No splitting or overlap: the longest chunk is ~310 characters.
- **PDPA:** chunk text and the user's question are masked before embedding (needed for the API backend; applied to
  local too for one code path). The full text stays only in the local SQLite file under `output/` (git-ignored).
- **Cost control:** API vectors are cached in SQLite by sha256(model + masked text); a rebuild embeds only new or
  changed chunks. Local vectors are recomputed each build (free, < 2 s). **Stale guard:** if the ingest outputs
  change, search reports `INDEX_STALE` and uses keyword until `build_index` is rerun.
- **Search (`search.py`)**: `mode="hybrid"` (default) fuses keyword ranks and vector ranks (reciprocal rank fusion,
  k=60); `mode="vector"`; `mode="keyword"` (never embeds). Exact paths unchanged: `category` → that rule row,
  `order_number` → that order's emails. Every result has `retrieval` (e.g. `hybrid:keyword+local-tfidf-chargram-v1`,
  `keyword (fallback: INDEX_MISSING)`). The query embedder always matches the model the index was built with.
- Also: question words (what, how, do, who, …) added to the keyword stopwords — they matched the guide's notes for
  unrelated questions.

## Measurements (real guide, 17 Nov; 19 questions = 16 from the 17 Nov guide handoff + 3 with typos; 5 unrelated)

| Mode | Right rule first | Typos caught | Unrelated → "no rule" |
|---|---:|---:|---:|
| keyword | 15/19 | 0/3 | 5/5 |
| vector (local) | 11/19 | 2/3 | 5/5 |
| **hybrid (default)** | **16/19** | **2/3** | **5/5** |

- Hybrid wins: it keeps keyword's strength on clear wording and adds typo tolerance ("delivry came very lat",
  "wrng adress deliverd"). It lost one keyword win ("extra cash on delivery" → Public holiday instead of COD).
- Misses for every mode: "item inside was smashed", "parcle thrwn ovr the gate", and (hybrid) the cash case.
  Pure synonyms ("smashed" = damaged) need a language-model embedding — the API backend — and are listed as a
  known limit, to retest when credit returns.
- Similarity cutoff for local vectors: **0.10** (unrelated questions scored 0.02–0.09). API cutoff 0.30 is
  provisional until the first API build.

## Checks

- 89 unit tests pass (19 for the index: build, cache reuse, masking of what is sent, kind filter, threshold,
  stale refusal, exact email citations from vector hits, order filter, fallbacks on endpoint failure / no index /
  no faiss / missing local model file, keyword mode never embeds, local typo tolerance, determinism).
- Evals: **21/21 pass** on the real data. A-E19..A-E21 now test typo tolerance and "no rule" for an unrelated
  question.

## Team API key: out of credit (found 17 Nov)

HTTP 429 `insufficient_quota / credit_balance_exhausted` for every model, embeddings **and gpt-4o-mini chat** — it
blocks C's agent too. A's logged spend is US$0.32 (81 calls, all 16 Nov 15:19–15:24 SGT); a scan of all 53 commits
found no key in the repo. Cause unknown (shared account, another member's usage, or credit not loaded); raise with
Leonard. Do not switch to the class key.

## Next Step

- Run: `pip install -r backend/unstructured/requirements.txt`, then `python -m backend.unstructured.ingest`,
  then `python -m backend.unstructured.build_index` (free with the local model).
- Jeffrey: realistic questions → re-measure the table above.
- When credit returns: `A_EMBED_MODEL=text-embedding-3-small` + `build_index` (< US$0.001), calibrate the 0.30 cutoff,
  and compare against the local model on the same questions.
- John (C): default `mode="hybrid"`; show `retrieval` in traces.
