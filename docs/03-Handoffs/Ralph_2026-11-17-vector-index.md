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
- **PDPA:** chunk text and the user's question go through `masking.privacy_guard` (incl. names and street
  addresses, see "PR #13 review fixes" below) before embedding (needed for the API backend; applied to local too for
  one code path). The full text stays only in the local SQLite file under `output/` (git-ignored).
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

- 89 unit tests passed at first push (now 106, see "PR #13 review fixes"; 19 for the index at first push: build, cache reuse, masking of what is sent, kind filter, threshold,
  stale refusal, exact email citations from vector hits, order filter, fallbacks on endpoint failure / no index /
  no faiss / missing local model file, keyword mode never embeds, local typo tolerance, determinism).
- Evals: **21/21 pass** on the real data. A-E19..A-E21 now test typo tolerance and "no rule" for an unrelated
  question.

## PR #13 review fixes (17 Nov, John's review)

**P1 — names and street addresses reached the API embedder.** `mask_text` only hid emails, phones, NRIC, unit,
postal and block; "Jane Tan" and "123 Orchard Road" went out as typed (reproduced). Fix:
- New `masking.privacy_guard()` = `mask_text` + street addresses + personal names. It covers titles (Mr/Mdm/Dr),
  patronymics (bin/binte/s/o), cues ("my name is", "Regards,", "Dear", "Customer:"), common Singapore given names
  and surnames in either order, and street forms ("123 Orchard Road", "Tampines St 11", "Ang Mo Kio Central",
  "Jalan Bukit Merah").
- It is applied to every chunk and every query before embedding, and **again inside the API embedder** right before
  the request, so a future caller cannot skip it. Idempotent, so the double pass changes nothing.
- Measured on the real data: **526/526** distinct customer/driver names and **25,833/25,833** order addresses fully
  masked. 0 of the 102 indexed chunks change, so retrieval on the real data is unchanged (same rankings as before
  on the sample questions; evals 21/21).
- The local embedder ignores the `[NAME]`/`[ADDRESS]` placeholders, so a masked street does not look like the word
  "address" and pull results towards the "Wrong address" rule.
- **Limit:** rule-based. A name with no title, no cue and not on the lists (e.g. a lone foreign first name) can still
  pass. The default embedder is local, so nothing leaves the machine unless `A_EMBED_MODEL` is set.

**P2 — a damaged index crashed search instead of falling back.** A half-written FAISS file raised a raw
`RuntimeError` (reproduced). Fix:
- Every way the index files can be bad now ends in `VectorUnavailable`, so hybrid falls back to keyword and says why:
  `INDEX_CORRUPT` (partial/unreadable FAISS, SQLite or local-model file, files from different builds, vector count
  ≠ chunk count), `INDEX_STALE` (older index format, or a query vector of the wrong size).
- Writes are safe: SQLite is one transaction; the FAISS and local-model files are written to a temp file, flushed
  and swapped in with `os.replace`. SQLite records the sha256 of both files, so a crash between the two steps is
  detected (`INDEX_CORRUPT`) instead of mapping vectors to the wrong citations. A failed write is `INDEX_WRITE_FAILED`.
- Index format is now `a-vec-2`. **Anyone with an older index: rerun `python -m backend.unstructured.build_index`**
  (free with the local model). Until then search says `keyword (fallback: INDEX_STALE)`.

Tests: 106 pass (17 new: 5 guard, 3 guard-in-index incl. the API boundary, 9 damaged-file and atomic-write cases).

## PR #14 review fixes (17 Nov evening, John + Copilot)

**P1 — casing and name-length gaps.** "Customer: JANE TAN at 12 bedok north drive" reached the embedder unchanged
(reproduced); several rules required Title Case, and lower-case three-part names leaked partially. Fix in
`privacy_guard`:
- Names after a field cue ("Customer:", "Name:", "From:", "my name is") are taken in any casing, up to 4 words.
- Titles, sign-offs and the name lists now catch ALL CAPS ("Mr TAN AH KOW", "Regards, JOHN", "ZHI WEI TAN") and
  lower case ("customer: jane tan", "tan mei ling", "lim jane", "ahmad bin yusof").
- Numbered addresses are caught in any casing ("12 bedok north drive", "12 BEDOK NORTH DRIVE"). Without a house
  number the Drive/Way/Place/... suffixes still need Title Case or CAPS, because they are everyday words.
- Copilot's items: single-letter apostrophe surnames ("Ryan D'Cruz"), surname-first before a given name ("Lim Jane
  Tan" is one name), three-word names after "my name is".
- One exclusion list (function words, titles, common verbs and the complaint vocabulary) stops the wider rules from
  eating complaint text: "mr tan said the parcel" keeps "said the parcel"; "low quality packaging", "SIM CARD
  MISSING" and "I AM VERY UPSET" are untouched.

**P2 — the greeting rule ate complaint text.** "Hi, Lat Parcle Apolgy" became "Hi, [NAME]", so the vector side had
nothing to match and the hybrid result was `not_found` (reproduced). Fix: after "Hi/Hello/Hey" a name is at most two
Title/CAPS words AND must be followed by a comma, full stop, line break or the end of the text ("Hi Jane," /
"Hello Zhi Wei"). Anything else after a greeting is complaint text and stays. Regression tests at three levels: the
guard, the fake embedder (it receives "Hi, Lat Parcle Apolgy" verbatim) and the local index (same top rule as
without "Hi,").

**Copilot (medium) — malformed index metadata.** A non-numeric or out-of-range `min_similarity` / `dim` in the index
database raised a raw `ValueError` inside `search`. Both are validated when the index is loaded and end in
`INDEX_CORRUPT` → keyword fallback with the reason.

- Checked against the real data: the guard output for all 102 indexed chunks and 26 sample questions is unchanged
  except the three greeting cases, so rankings and evals (21/21) are the same as before.
- Index format is now `a-vec-3` (the guard changed, so embedded text could change). **Rerun
  `python -m backend.unstructured.build_index`** (free). Until then search says `keyword (fallback: INDEX_STALE)`.
- Remaining limits (documented, not fixed): an unknown lower-case name with no cue ("zhi wei tan" all in lower case),
  and a typo'd capitalised two-word complaint that ends a greeting line ("Hi Lat Parcle" with nothing after it).

Tests: 120 pass (14 new: 9 guard casing/greeting cases; 5 index: the greeting reaches the embedder, CAPS and
lower-case names never do, two bad-metadata fallbacks, local-index typo tolerance with a greeting).

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
