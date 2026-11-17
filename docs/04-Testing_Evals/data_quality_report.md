# Data Quality Report

- One-page report of data problems and handling
- B compiles; all contribute

## A — Emails, delivery photos, rate card, rule book (Ralph, 17 Nov)

| Problem found | Evidence | How the app handles it |
|---|---|---|
| Customers' claims contradict the records: 33 of 82 complaints (block numbers 0 of 17 match; "still in transit" 0 of 16) | [email findings §4](../05-Reviews/email_observations_2026-11-17.md#4-customer-claims-do-not-match-the-records) | Quotes the record with its source, never the customer's claim |
| Almost no photo evidence: all 80 photos are Oct–Nov 2025, complaints Mar–Jun 2026. Only 1 complaint (order 22574) has a photo, 8 months older, probably a different order | [email findings §3](../05-Reviews/email_observations_2026-11-17.md#3-almost-no-proof-of-delivery-to-tally-against) · [trap T-A06](../05-Reviews/trap_list_2026-11-16.md#a--unstructured-sources-found-16-nov-2026-ralph--developer-a) | Says "no POD on file" (client answer Q04); never reuses another order's photo |
| Same order number in both systems: 47 of 82 complaint numbers fit old and new; no email says which | [data audit A2](../05-Reviews/data_audit_2026-11-16.md#a2-complaint-emails-90) · [trap T-A01](../05-Reviews/trap_list_2026-11-16.md#a--unstructured-sources-found-16-nov-2026-ralph--developer-a) | Never picks silently: date check, then the client's case log (73 of 79 senders listed with an order ref), else asks. B's order lookup |
| Delivery slips disagree with the database or themselves: cash amounts differ on all 9 slips that mention cash; 7 say "left outside" yet are signed | [data audit A3](../05-Reviews/data_audit_2026-11-16.md#a3-pod-scans-80) | Shows both values, each with its source (agreed 17 Nov) |
| Rule book missing from the zip; only one rate card (from 1 Apr 2026) for 17,195 earlier orders; weight bands overlap at 3 and 10 kg | [package check](../05-Reviews/package_reconciliation_2026-11-16.md) · [data audit A4](../05-Reviews/data_audit_2026-11-16.md#a4-rate-card-1) · [client answers](../00-Biz_Requirements/client_qa_v02.xlsx) | Asked the client: rule book received; April card used for all orders, labelled "applied retrospectively, per client"; upper band limit inclusive (Q06/Q07) |

Every fact carries its source (file, photo field, email position or Excel row: [citation format](../02-Design/contracts_2026-11-16.md#1-citation-shared-by-every-a-tool)).
The AI read all 80 photos and the rate card once for US$0.32 and matched the database on every key field, 80 of 80 ([cost log](api_spend.md)).
