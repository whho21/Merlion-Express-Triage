# backend/unstructured — Developer A

Emails, the Resolution Guide (policy), proof-of-delivery (POD) cards and rate cards → cited records and search
tools for B and C. Standard library only (any Python 3.9+), so nothing to install.

**Records are unmasked on purpose** (John, 16 Nov): A extracts everything; B/C/D hide personal data before the AI
model or a customer sees it. `masking.py` is a ready helper they can reuse. Outputs live in `output/unstructured/`
(git-ignored — they hold real personal data; never commit or copy them elsewhere).

## Run (from the repo root, after unzipping the package into `data/`)

```bash
python -m backend.unstructured.ingest                         # emails + policy -> emails.jsonl, policy_chunks.jsonl, manifest.json (free)
python -m backend.unstructured.extract_images --dry-run       # free: how many images would be sent to the model
python -m backend.unstructured.extract_images --limit 2       # paid smoke test (2 POD cards + the rate card)
python -m backend.unstructured.extract_images                 # paid: every image not already cached
python -m backend.unstructured.evals                          # A's 12 eval cases: PASS / FAIL / PENDING
python -m unittest discover -s backend/unstructured/tests -t .   # 63 unit tests, synthetic data, no network
```

The image run needs the **team** key: `OPENAI_API_KEY=` in this repo's own `.env` (from the team's NTULearn item).
It never reads a `.env` in a parent folder, so the class key is never spent by accident. Optional settings:
`A_VISION_MODEL` (default `gpt-4o-mini`), `OPENAI_BASE_URL`. Every run appends its estimated cost to
`output/unstructured/spend_log.jsonl` and prints the running total against the US$50 team budget; the shared
record is `docs/04-Testing_Evals/api_spend.md`. First full run (16 Nov): 81 images, about US$0.32.

## Files

| File | What it does |
|---|---|
| `emails.py` | Keeps sender, recipient, subject and body as written; 7 categories (+ `unclassified`); order numbers, driver codes, corporate account and customer claims, each with a `body:char:<a>-<b>` locator. |
| `policy.py` | Finds the guide under `data/tabular/` or `data/docs/`; `.md`/`.txt` by heading, `.csv` by row. Today: `SOURCE_MISSING` (client question A-Q1). |
| `ingest.py` | Runs both; writes outputs + a per-file manifest; prints counts only. |
| `llm.py` | Calls the class vision endpoint: JSON answers, 3 bounded retries, one telemetry line per call (no content). |
| `cache.py` | Caches each answer by image hash + prompt version + model, so reruns cost nothing (task 6). |
| `sqlref.py` | Read-only reference from the SQL dump to validate POD cards (B still owns the database). |
| `pod.py` | POD prompt, normalisation (day-first dates, look-alike fixes, receiver kind), confidence, SQL validation, flags, `find_pod`. |
| `ratecard.py` | Rate-card prompt and parsing (bands, prices, surcharges, notes) and `lookup_rate` (not_found before the card's date, ambiguous on band edges). |
| `extract_images.py` | Runs POD + rate-card extraction with cache, manifest, telemetry and SQL validation. |
| `search.py` | `search_emails(query, order_number=None)` and `search_policy(query, effective_date=None)` for C, with exact citations. |
| `evals.py` | Runs `evals/developer_a_cases.json`. |
| `masking.py` | Shared helper for B/C/D: masks emails, NRIC, phones, unit numbers, postal codes, block numbers (not names). |

Record shapes, envelopes and telemetry: `docs/02-Design/contracts.md` sections 2–6. Traps: `docs/05-Reviews/trap_list.md`.
Limits and evidence for B/C/D: `docs/03-Handoffs/Ralph_2026-11-16-A-tools-evidence-limits.md`.

## Not done here (on purpose)

- Choosing v1 vs v2 for an email's order number — B's candidate lookup (T-A01). A passes the number and the email date.
- Masking — B/C/D (John, 16 Nov).
