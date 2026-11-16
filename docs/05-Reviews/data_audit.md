# Data audit — released package

**Checked:** 16 Nov 2026, SGT. **Status:** Initial technical sanity review; full semantic audit remains open.
**Package root:** `data/team2_merlion_express_package/` (local, Git-ignored).
**Owners:** A/Ralph (unstructured), B/Jenn Fang (structured); E/Wai Hong reconciles package/setup checks; C/John reviews cross-source assumptions.

## Method and limits

Read the package brief and both briefing PDF pages. Read the full SQL dump, all GPS JSONL lines and all 90 email text files. Opened all 81 JPEG files with Pillow integrity verification; visually inspected the rate card. Parsed the SQL CREATE/INSERT statements into an in-memory SQLite database for aggregate checks; no client records were committed or written into a replacement dataset. This is not evidence that a developer's running MySQL instance has loaded correctly, nor a MySQL compatibility/performance test. Each developer must independently check local MySQL using [seeding instructions](../../scripts/seed_sql_data.md).

JPEG decoding is not a full visual/OCR audit of every POD. Email readability is not successful order resolution. Epoch conversion alone does not establish the business timezone or a correction. Retain these distinctions when reporting checkpoint completion.

## Inventory and observed counts

| Source relative to package root | Observed | Check completed | Remaining |
|---|---:|---|---|
| `sql/merlion_ops.sql` | 1 dump; 3 tables | Parsed; aggregate key/join/null checks below | Validate native MySQL loads, indexes, cleaning and repeatability |
| `logs/gps_pings_sample.jsonl` | 60,000 records | 0 JSON parse failures; common keys `driver`, `ts`, `lat`, `lon`, `speed_kmh` | Time alignment, duplicate pings, driver/time coverage and relevance |
| `docs/complaint_emails/` | 90 text files | All readable, non-empty and contain a Date header | Semantic extraction, identities, duplicates, complaint dates and attribution |
| `images/proof_of_delivery/` | 80 JPEGs | All decode; filenames all identify v1; all filename order keys match orders | Visual/OCR accuracy, source conflicts, coverage expectations |
| `images/rate_cards/` | 1 JPEG | Decodes; visually read effective date: 1 April 2026 | Validated structured extraction; historical coverage; applicability rules |
| `tabular/` | 0 files | Directory exists but is empty | Obtain CS case log and Resolution Guide; Q01/Q02 |
| `CLIENT_BRIEF.md` | 1 file | Read; compared expected sources with package | Track clarifications rather than invent absent rules |
| `BRIEFING_team2_merlion_express.pdf` | 1 file, 2 pages | Text read | Its old checkpoint date is superseded by team instruction; preserve original |

There are 175 non-OS-metadata files. Ignore `.DS_Store` when reconciling business inputs.

## Structured-data sanity

| Check | Observed result | Interpretation/action |
|---|---|---|
| Drivers | 40 rows | Use `driver_id` / `driver_code`, not a person's name, for identity |
| Orders | 25,833 rows: v1 11,499; v2 14,334 | System-aware identity is essential |
| Deliveries | 24,802 rows | Keep order status separate from observed delivery evidence |
| Order dates | v1: 1 Oct 2025–31 Jan 2026; v2: 1 Feb–30 Jun 2026 | Migration boundary visible in supplied data |
| Cross-system order-number reuse | 11,499 IDs occur in both systems | Never join or resolve by `order_id` alone |
| Duplicate `(system_version, order_id)` | 0 | Candidate cleaned primary key; raw `orders` declares no primary key |
| Null cells in the three supplied tables | 0 SQL NULL values | Does not establish that strings or business values are valid |
| Postal codes | All 25,833 are six numeric characters | Brief's malformed-postal-code issue not reproduced by this check; semantic validity remains unverified |
| Delivery → order joins using both keys | 0 orphan references | Preserve the composite join in tools |
| Delivery → driver joins using ID | 0 orphan references | GPS uses driver codes; map through the driver table |
| Orders without a delivery row | 1,031 | Investigate status/coverage; do not label all as failed or corrupt |
| Multiple delivery rows per composite order key | 0 | Current export provides at most one event; cannot infer a complete attempt history |
| Duplicate driver-name groups | 6 | Driver names are not reliable unique identifiers |
| Delivery outcomes | 21,865 delivered; 2,177 failed attempts; 760 returned | Outcomes are not equivalent to complaint counts |
| Orders before supplied rate-card effective date | 17,195 | Earlier pricing unsupported without clarification; Q03 |
| Explicit zone/service-tier columns | Not present in supplied SQL tables | Do not infer a business mapping without an agreed rule; Q04 |

## GPS and image coverage

- All 60,000 GPS records have valid latitude/longitude ranges and non-negative speeds. Their 40 distinct driver codes match the supplied driver codes. This is an integrity check, not proof of delivery/location relevance.
- Epoch timestamps span **30 Sep 2025 15:02:59 UTC–30 Jun 2026 06:56:48 UTC**. Confirm source semantics and align driver/time windows before applying any offset; Q06.
- POD filename keys match orders but all 80 are labelled v1. No v2-labelled PODs were found. Absence from this export is not proof that delivery did not occur; Q05.
- The rate card starts 1 April 2026 and says it supersedes previous cards. Do not apply it retroactively to earlier orders without authority. No prior card was found.

## Open work before full audit sign-off

- [ ] B reproduce counts in native MySQL; all five verify their own setup.
- [ ] A visually inspect every POD, validate OCR fields/uncertainty and test image-to-order links beyond filenames.
- [ ] A/B resolve email identities and record ambiguity and cross-source coverage.
- [ ] B check GPS duplicates, timezone alignment, sparse coverage and order/delivery status consistency.
- [ ] B investigate postal-code semantic issues without inventing replacement values.
- [ ] A/B audit case log and Resolution Guide when supplied; audit any additional rates/rules received.
- [ ] B reconcile cleaned/loaded/rejected/duplicate counts and repeated-load behaviour.
- [ ] C/E turn confirmed traps into checkable evals; owners verify expected answers.

See [package checklist](package_checklist.md), [trap list](trap_list.md) and [client Q&A](../00-Biz_Requirements/client_qa.md). Client questions are drafted, not sent or answered.
