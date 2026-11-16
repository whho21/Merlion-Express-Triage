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
| CS case log in `tabular/` | Directory empty | Missing locally; B, Q01 drafted and unsent |
| CS Resolution Guide | No guide found in package files | Missing locally; A/B, Q02 drafted and unsent |
| Supporting briefing / brief | PDF (2 pages), `CLIENT_BRIEF.md` | Present; preserve originals |

Before reporting missing files as a supplier omission, E and B check the original downloaded archive/NTULearn item for incomplete extraction or a separately supplied attachment. That comparison has not yet been performed. Raise unresolved gaps promptly; do not silently substitute other sources.

- [ ] Original archive / separate attachments checked.
- [ ] John sends reviewed client questions and records date sent.
- [ ] Responses and any new files reconciled; audit updated.
- [ ] All five developers verify equivalent local package and database counts.

Technical results and limits: [data audit](data_audit.md). Questions/status: [client Q&A](../00-Biz_Requirements/client_qa.md). A question drafted in the log is not evidence that the client has been contacted.
