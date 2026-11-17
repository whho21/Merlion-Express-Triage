# Package reconciliation

**Checked:** 16 Nov 2026. Package root: `data/team2_merlion_express_package/`.
**Owner:** E/Wai Hong maintains the checklist; A/Ralph and B/Jenn Fang verify their sources; John coordinates client communication.

| Expected from brief | Observed locally | Status / owner / next action |
|---|---|---|
| SQL operations dump | `sql/merlion_ops.sql`; 3 tables | Present; B validates native MySQL counts and cleaned schema |
| GPS sample, about 60k pings | `logs/gps_pings_sample.jsonl`; 60,000 parseable lines | Present; B investigates time alignment |
| 80 POD scans | 80 JPEGs under `images/proof_of_delivery/`, all v1-labelled | Count matches; A verifies contents and expected coverage, Q05 |
| Rate-card images | `images/rate_cards/rate_card_apr2026.jpg` only | Present but historical coverage unresolved; A/B, Q03/Q04 |
| 90 complaint emails | 90 non-empty readable text files | Count matches; A verifies identities/content |
| CS case log in `tabular/` | Directory empty | **Received 16 Nov 8:00 PM** with the client's Q01 reply: `CS_case_log_Oct25-Jun26.xlsx`, tab "Case Log" (505 rows; names and phone numbers — keep in `tabular/`, git-ignored). B |
| CS Resolution Guide | No guide found in package files | **Received 16 Nov** as tab "Resolution Guide" of the same workbook (v2, 2 Mar 2026; 9 rules + 3 notes; Q02). A parses it (`search_policy`) |
| Supporting briefing / brief | PDF (2 pages), `CLIENT_BRIEF.md` | Present; preserve originals |

Ralph reports that `tabular/` is absent from the archive (see below); the local package has an empty directory. E and B should independently reconcile the archive and check for separately supplied attachments before reporting a supplier omission. Raise unresolved gaps promptly; do not silently substitute other sources.

- [ ] Original archive / separate attachments checked.
- [x] John sends reviewed client questions and records date sent — sent 16 Nov 6:42 PM; client replied Q01–Q08
      16 Nov 8:00 PM. Ralph's A-Q1..A-Q4 are covered by Q01–Q08. A-Q5 (email → order link) is answered by the data:
      73 of 79 complaint senders appear in the case log "Contact" column with an "Order Ref" (for B).
- [ ] Responses and any new files reconciled; audit updated.
- [ ] All five developers verify equivalent local package and database counts.

Technical results and limits: [data audit](data_audit.md). Questions/status: [client Q&A](../00-Biz_Requirements/client_qa.md). A question drafted in the log is not evidence that the client has been contacted.
## A's package reconciliation

**Package:** `team2_merlion_express_package.zip` (NTULearn, 16 Nov 2026), 176 entries, 14.8 MB unzipped. No
executables or scripts inside. Unzipped into `data/` (git-ignored).
**Brief:** `docs/00-Biz_Requirements/CLIENT_BRIEF.md`, "Data manifest" (line 20) and deliverable 2 (line 34:
"Ingestion of ALL data source types in this package (SQL, tabular, images, documents)").

## Expected vs received

| Manifest item (brief) | Expected | Received | Status | Owner | Client question |
|---|---|---|---|---|---|
| `sql/merlion_ops.sql` | Ops SQL dump, v1 + v2 | 1 file, 5.8 MB (tables: drivers, orders, deliveries) | ✅ Received, B to profile | B | — |
| `tabular/` | CS case log **and** Resolution Guide | **Folder absent** | ❌ Missing from the zip → ✅ **received separately 16 Nov** | B inventories / A retrieves | **A-Q1 → answered 16 Nov (John's Q01/Q02): workbook received** |
| `logs/gps_pings_sample.jsonl` | ~60k GPS pings | 1 file | ✅ Received, B to count/profile | B | — |
| `images/proof_of_delivery/` | 80 scans | 80 JPG, **all v1** (orders Oct–Nov 2025) | ⚠️ Count OK, **no v2 scans** | A | **A-Q3 → answered (Q04): no POD after 1 Feb 2026, say so plainly** |
| `images/rate_cards/` | rate card image(s) | 1 JPG, effective 1 Apr 2026 | ⚠️ **No card before 1 Apr 2026** | A | **A-Q2, A-Q4 → answered (Q06/Q07/Q08): April card applies to all; upper limit inclusive; standard only** |
| `docs/complaint_emails/` | 90 emails | 90 TXT | ✅ Received | A | A-Q5 → answered by the case log: 73/79 senders listed with an Order Ref |
| *(not in manifest)* `BRIEFING_team2_merlion_express.pdf`, `CLIENT_BRIEF.md` | — | 2 files at zip root | ℹ️ Identical to repo copies | — | — |

## Questions drafted by A (to captain for consolidation, 16 Nov)

Status: **sent and answered.** John folded these into the team's Q01–Q08, sent them 16 Nov, 6:42 PM (subject
`Client question — Team 2`), and the client answered the same evening, 8:00 PM. Replies are logged in
`docs/00-Biz_Requirements/client_qa_v02.xlsx`; the table above shows which answer covers each A question.

| ID | Question | Why it blocks us |
|---|---|---|
| A-Q1 | The brief lists `tabular/` (CS case log + Resolution Guide), but the package has no `tabular/` folder. Please send both files. | No Resolution Guide = no policy-based recommendation (re-deliver/refund/compensate/reject). No case log = no weekly driver/zone complaint view. Tabular is also one of the source types the brief requires. |
| A-Q2 | The only rate card is effective 1 Apr 2026 and "supersedes all previous". Please send the earlier card(s), or confirm the April card applies to all earlier orders. | v1 orders (Oct 2025–Jan 2026), v2 Feb–Mar 2026 and 20 March complaints have no applicable rate. |
| A-Q3 | All 80 POD scans are v1 orders from Oct–Nov 2025. Are there POD scans for v2 orders (Feb–Jun 2026)? If not, should "no POD on file" be treated as missing evidence? | Every complaint is dated Mar–Jun 2026. Only 1 complaint number matches a scan, and that scan is probably from the other system. |
| A-Q4 | The weight bands overlap (≤3 kg / 3–10 kg / 10–25 kg). Which band applies at exactly 3 kg and 10 kg? How do postal codes map to the four zones, and where is the service type (standard vs same-day) recorded? | 13 orders weigh exactly 3.00 kg and 7 exactly 10.00 kg. `orders` has no zone or service-type column. |
| A-Q5 | Customers never say V1 or V2, and the orders table has no email address. Is there a customer contact table that links sender emails to orders? | 47 of 82 complaint numbers exist in both systems with plausible dates. 12 match no order that existed when the email was sent. |

**Timing risk:** the client replies within two working days. Sent by Tue 17 Nov → answer by Thu 19 Nov at the earliest,
one day before Checkpoint 1 (Fri 20 Nov 17:00). **Outcome:** John sent 16 Nov 6:42 PM, client answered the same evening, so no timing risk materialised.
