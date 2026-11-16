# Package Checklist

- Package checked against the brief in docs/package_checklist.md; missing items raised with client and answers recorded when received. Mark pending replies explicitly and raise timing risk at the consult.
- A/B

**Package:** `team2_merlion_express_package.zip` (NTULearn, 16 Nov 2026), 176 entries, 14.8 MB unzipped. No
executables or scripts inside. Unzipped into `data/` (git-ignored).
**Brief:** `docs/00-Biz_Requirements/CLIENT_BRIEF.md`, "Data manifest" (line 20) and deliverable 2 (line 34:
"Ingestion of ALL data source types in this package (SQL, tabular, images, documents)").

## Expected vs received

| Manifest item (brief) | Expected | Received | Status | Owner | Client question |
|---|---|---|---|---|---|
| `sql/merlion_ops.sql` | Ops SQL dump, v1 + v2 | 1 file, 5.8 MB (tables: drivers, orders, deliveries) | ✅ Received, B to profile | B | — |
| `tabular/` | CS case log **and** Resolution Guide | **Folder absent** | ❌ **Missing** | B inventories / A retrieves | **A-Q1 (pending)** |
| `logs/gps_pings_sample.jsonl` | ~60k GPS pings | 1 file | ✅ Received, B to count/profile | B | — |
| `images/proof_of_delivery/` | 80 scans | 80 JPG, **all v1** (orders Oct–Nov 2025) | ⚠️ Count OK, **no v2 scans** | A | **A-Q3 (pending)** |
| `images/rate_cards/` | rate card image(s) | 1 JPG, effective 1 Apr 2026 | ⚠️ **No card before 1 Apr 2026** | A | **A-Q2, A-Q4 (pending)** |
| `docs/complaint_emails/` | 90 emails | 90 TXT | ✅ Received | A | A-Q5 (pending) |
| *(not in manifest)* `BRIEFING_team2_merlion_express.pdf`, `CLIENT_BRIEF.md` | — | 2 files at zip root | ℹ️ Identical to repo copies | — | — |

## Questions drafted by A (to captain for consolidation, 16 Nov)

Status: **drafted, not yet sent**. The captain consolidates and sends to the course director, subject
`Client question — Team 2`. Answers go in `docs/00-Biz_Requirements/client_qa.md`.

| ID | Question | Why it blocks us |
|---|---|---|
| A-Q1 | The brief lists `tabular/` (CS case log + Resolution Guide), but the package has no `tabular/` folder. Please send both files. | No Resolution Guide = no policy-based recommendation (re-deliver/refund/compensate/reject). No case log = no weekly driver/zone complaint view. Tabular is also one of the source types the brief requires. |
| A-Q2 | The only rate card is effective 1 Apr 2026 and "supersedes all previous". Please send the earlier card(s), or confirm the April card applies to all earlier orders. | v1 orders (Oct 2025–Jan 2026), v2 Feb–Mar 2026 and 20 March complaints have no applicable rate. |
| A-Q3 | All 80 POD scans are v1 orders from Oct–Nov 2025. Are there POD scans for v2 orders (Feb–Jun 2026)? If not, should "no POD on file" be treated as missing evidence? | Every complaint is dated Mar–Jun 2026. Only 1 complaint number matches a scan, and that scan is probably from the other system. |
| A-Q4 | The weight bands overlap (≤3 kg / 3–10 kg / 10–25 kg). Which band applies at exactly 3 kg and 10 kg? How do postal codes map to the four zones, and where is the service type (standard vs same-day) recorded? | 13 orders weigh exactly 3.00 kg and 7 exactly 10.00 kg. `orders` has no zone or service-type column. |
| A-Q5 | Customers never say V1 or V2, and the orders table has no email address. Is there a customer contact table that links sender emails to orders? | 47 of 82 complaint numbers exist in both systems with plausible dates. 12 match no order that existed when the email was sent. |

**Timing risk:** the client replies within two working days. Sent by Tue 17 Nov → answer by Thu 19 Nov at the earliest,
one day before Checkpoint 1 (Fri 20 Nov 17:00). Until answered, A-Q1 blocks policy search and the weekly view.
