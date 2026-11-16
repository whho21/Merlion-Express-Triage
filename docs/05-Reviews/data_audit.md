# Data Audit

- Every file opened; row/page/file counts recorded in docs/data_audit.md
- Counts, source coverage, parsing and join findings

Sections: **A — Unstructured sources** (this section) · **B — Structured sources** (SQL, tabular, GPS: B to add).
Package unzipped from `team2_merlion_express_package.zip` (NTULearn, 16 Nov 2026). No client records are copied
here: evidence cites file names, order numbers and driver codes only. Names, phone numbers, email addresses and
street addresses stay in `data/` (git-ignored).

---

## A — Unstructured sources (Developer A)

**Audited:** 16 Nov 2026 by Ralph (proposed Developer A; role confirmation pending at the 17 Nov sync).
**Method:** every file was opened. The 80 POD scans and the rate card were read visually, one by one. Emails were
parsed by script (headers, order numbers, templates). Every extracted value was then cross-checked against
`sql/merlion_ops.sql`, which was parsed read-only and not loaded into MySQL.

### A1. Inventory and counts

| Source | Brief says | Received | Opened | Parse / read status |
|---|---|---:|---:|---|
| `docs/complaint_emails/*.txt` | 90 emails | **90** | 90 | All UTF-8, 248–312 bytes. All 4 headers (`From`, `To`, `Date`, `Subject`) present and parseable in every file |
| `images/proof_of_delivery/*.jpg` | 80 scans | **80** | 80 | All 80 readable by eye. No field unreadable. JPG, 30–60 KB |
| `images/rate_cards/*.jpg` | "rate cards" (no count) | **1** | 1 | `rate_card_apr2026.jpg`, readable |
| Resolution Guide (policy) | inside `tabular/` | **0** | — | **Missing**: no `tabular/` folder in the zip (see package checklist) |
| `BRIEFING_team2_merlion_express.pdf` (zip root) | not in manifest | 1 | 1 | 2 pages. Byte-identical to `docs/00-Biz_Requirements/` copy |
| `CLIENT_BRIEF.md` (zip root) | not in manifest | 1 | 1 | Identical to `docs/00-Biz_Requirements/CLIENT_BRIEF.md` |

### A2. Complaint emails (90)

| Check | Result |
|---|---|
| Date range | 2026-03-02 → 2026-06-30. All `+0800`. File-name date equals the `Date:` header in 90/90 |
| Per month | Mar 20 · Apr 18 · May 24 · Jun 28 |
| Recipient | All to the support address |
| Senders | 79 distinct; 10 senders wrote more than once (max 3). Personal free-mail addresses (PII) |
| Templates | **7 subjects only**: Wrong address delivered 17 · Item missing from parcel 16 · Where is my parcel?! 16 · COD amount wrong 14 · Late again — third time 11 · **Compliment for driver 8** · Parcel thrown over gate 8 |
| Order numbers | 82 emails have exactly one 5-digit number. 8 have none (all 8 are compliments, which name a driver code instead). **No email says V1 or V2** |
| Number → system (date-plausible) | **47 ambiguous** (exists in v1 and v2, both dated before the email) · 21 only v1 plausible · 2 only v2 · **12 impossible** (only a v2 order exists and it is dated after the email) |
| Corporate | 11 emails (all "Late again") cite account `MERL-C-0042` and say "Orders N and others" (only one order listed) |
| PII in body | 16 contain a phone number · 17 contain block numbers · all senders' addresses are name-based |

### A3. POD scans (80)

| Check | Result |
|---|---|
| System | **All 80 are v1** (`POD_v1_<order>.jpg`). **0 POD scans for v2 orders** |
| Card dates | 02/10/2025 → 01/12/2025 (order dates 2025-10-01 → 2025-11-28). **No overlap with the complaint period (Mar–Jun 2026)** |
| Order ref vs file name | 80/80 match |
| Card vs SQL (v1) | Order exists 80/80. **Date/time equals `deliveries.delivered_time` to the minute 80/80.** Driver equals driver code 80/80. Postal code equals `orders.postal_code` 80/80. Block equals SQL address block 80/80 |
| Date format | `DD/MM/YYYY HH:MM`, confirmed by the SQL match (e.g. `02/10/2025` = 2 Oct) |
| Scan quality | Most cards rotated ~1–3° with faint circular stains. **No stain hides a key value**; stains touch the signature on several cards. On `POD_v1_24377` the monospace "1" in the day looks like a letter "I" (OCR risk; SQL confirms 18/11) |
| Template variants | **26/80** have the footer "Thank you for shipping with Merlion Express!" instead of the hotline footer. At least 8 cards print one label or line in italic (`21604`, `22201`, `22220`, `24316`, `24410`, `24495`, `24876`, `25207`); on `24410` and `24876` it is the Date/Time line (values still match SQL) |
| Times | 2 outside 07:00–22:00: `20135` 22:51, `23025` 22:42 (both match SQL) |
| Received by | **27/80 give a role, not a name** ("mum", "neighbour", "front desk", "domestic helper"); several more are a single word. "Front desk" appears at HDB block addresses |
| Signature | Present on 80/80, including cards whose remark says the parcel was left outside |
| Remarks | 6 stock phrases + blank. **Card remark agrees with `deliveries.remarks` on only 7/80** (6 both blank, 1 both "neighbour") |
| COD | 9 cards say "COD collected $X". **SQL `cod_amount` is 0 for 8 of them**; `24002` card $121 vs SQL $211.86. 17 POD orders have SQL `cod_amount` > 0, and only 1 of those cards mentions COD |

### A4. Rate card (1)

| Check | Result |
|---|---|
| Validity | "STANDARD RATE CARD — EFFECTIVE 1 APRIL 2026 (supersedes all previous)". **No earlier card in the package.** v1 orders (Oct 2025–Jan 2026), v2 Feb–Mar 2026 and the 20 March complaints all predate it |
| Structure | 4 zones (Central · East/North-East · North/West · Sentosa/Jurong Island) × 3 weight bands (≤3 kg · 3–10 kg · 10–25 kg) + same-day surcharge column, plus a "CBD ERP hours (0730–1900)" surcharge row |
| Notes on card | COD handling 1.5% (min $2.00) · re-attempt $3.00 from 3rd attempt · no standard delivery on public holidays, express PH = 2× standard · rates before GST (9%) · corporate rebate 5% above 2,000 parcels/month · Sentosa same-day "not available" |
| Boundaries | **Bands overlap at 3 kg and 10 kg.** SQL has 13 orders at exactly 3.00 kg and 7 at exactly 10.00 kg. Max weight in SQL 24.0 kg (none above 25 kg) |
| Inputs it needs | **Zone and service type (standard/same-day) are not columns in `orders`.** No postal-code → zone mapping in the package |
| Scan quality | Slight rotation, coffee-ring stains near values; every value legible |

### A5. Cross-source linkage (emails ↔ POD ↔ SQL)

- **Only 1 of 82 complaint order numbers has a POD scan in the package**: `22574` (`2026-06-19_014.txt`). That scan is
  the **v1** order delivered 29/10/2025, 235 days before the email; v2 `22574` was ordered 2026-02-27. The block the
  customer quotes from "the POD photo" matches neither the card nor SQL (v1 or v2).
- The 17 "Wrong address" emails all cite "the POD photo shows blk N". The package has a scan for only one of them,
  and in **17/17** neither quoted block matches the SQL address block for that number in either system.
- The 16 "Where is my parcel" emails say "ordered N days ago … still IN_TRANSIT". In **0/16** does SQL show an order
  with that number placed N days before the email and still in transit.
- `deliveries.remarks` and the POD card remarks use different vocabularies (SQL: handed to neighbour / gate locked /
  left at riser / called no answer).

### A6. What A will build from this (input to Stage 2)

- Emails: parse headers + body by code; classify by subject template; extract order number, driver code, corporate
  account, claimed amounts/blocks/days. **Mask phone numbers and sender addresses before any LLM call.**
- POD: extract fields with the class vision endpoint, validate against SQL (all 80 should match). Record uncertainty
  and keep the image path as the citation.
- Rate card: extract once into a versioned table (`effective_from` 2026-04-01), with explicit band-boundary rules
  once the client answers.
- Policy search: **blocked** until the Resolution Guide arrives.
