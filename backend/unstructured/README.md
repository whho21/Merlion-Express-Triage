# backend/unstructured — Developer A

Complaint emails and the Resolution Guide (policy) → masked, cited records. POD and rate-card extraction come
next (task 5). Standard library only, no LLM calls, so no API spend.

## Run (from the repo root, after unzipping the package into `data/`)

```bash
python -m backend.unstructured.ingest                              # data/ → output/unstructured/
python -m unittest discover -s backend/unstructured/tests -t .     # 28 tests, synthetic data only
```

Outputs go to `output/unstructured/` (git-ignored, never commit): `emails.jsonl`, `policy_chunks.jsonl`, and
`manifest.json` with one outcome per input file (sha256, parser version, status, issues). Exit code is 1 if the
email folder is missing or any email fails, so failures are visible.

## Files

| File | What it does |
|---|---|
| `masking.py` | Masks emails, NRIC, SG phone numbers, unit numbers, postal codes and block numbers. Names in free text are **not** detected — C's output guardrail must still check. |
| `emails.py` | Parses headers/body, sorts into 7 categories (+ `unclassified`), pulls order numbers, driver codes, corporate account and customer claims, each with a `body:char:<a>-<b>` locator. Stores a hashed `sender_id`, never the address. |
| `policy.py` | Finds the guide by name under `data/tabular/` or `data/docs/`, splits `.md`/`.txt` by heading and `.csv` by row. Today it records `SOURCE_MISSING` (client question A-Q1). |
| `ingest.py` | Runs both, writes outputs and the manifest, prints a summary with no personal data. |

Record shapes and rules: `docs/02-Design/contracts.md` section 4. Traps: `docs/05-Reviews/trap_list.md`.

## Not done here (on purpose)

- Choosing v1 vs v2 for an order number — B's candidate lookup (trap T-A01). This code passes the number and the
  email date.
- `search_emails` / `search_policy` tools — task 7, on top of these records.
