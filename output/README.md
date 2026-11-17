# README — Developer A result files (Ralph, 17 Nov 2026)

## What this is

The delivery-photo and rate-card results from A's code. They were made with
paid AI on 16 Nov (US$0.32).

## Private

These files hold customer names, phones and addresses.
Keep them in this Drive folder only (team members). Never put them in Git or
Discord. Delete them after the demo on 27 Nov.

## The files

1. `pod_records.jsonl` — 80 delivery photos, one record each: what the slip
   says, how sure the AI was, and the check against the database (key fields
   match 80 of 80).
2. `rate_cards.jsonl` — The April 2026 rate card as a price table (12 prices,
   surcharges and notes).
3. `image_manifest.json` — One line per image: read OK or failed, and where
   the result went.

## How to use (everyone)

1. Put the 3 files in your copy of the project:

   ```
   team2_merlion_express\output\unstructured\
   ```

2. Make the rest yourself. Free, no AI key needed. From the project folder:

   ```bash
   python -m backend.unstructured.ingest
   pip install -r backend/unstructured/requirements.txt
   python -m backend.unstructured.build_index
   ```

   `ingest` needs the client's Excel (`CS_case_log_Oct25-Jun26.xlsx`, from the
   client's 16 Nov email) in your `data\tabular\` folder.

3. Check it works:

   ```bash
   python -m backend.unstructured.evals
   ```

   You should see: **21 pass, 0 fail**.

4. Use the tools: `search_policy`, `search_emails`, `find_pod`, `lookup_rate`.
   Details: `backend/unstructured/README.md` on GitHub.

## Do not run

```bash
python -m backend.unstructured.extract_images
```

Without A's saved AI answers it calls the paid AI, which has no credit, and
it would overwrite these good files with failed ones. If you need it, ask
Ralph for the "cache" folder first.

---

Questions: Ralph (Developer A).
